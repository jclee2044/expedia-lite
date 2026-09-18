import shutil
import sqlite3
from pathlib import Path

import pytest

from backend.controllers.database import (
    DEFAULT_DATABASE_PATH,
    DatabaseVersionError,
    allocate_booking_id,
    allocate_user_id,
    connect_database,
    create_schema,
    initialize_database,
)
from backend.controllers.seed import SeedDataError, SeedStateError

DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"


def test_default_database_path_uses_backend_db_directory() -> None:
    assert DEFAULT_DATABASE_PATH.parent.name == "db"
    assert DEFAULT_DATABASE_PATH.name == "expedia_lite.sqlite3"


def _counts(connection: sqlite3.Connection) -> dict[str, int]:
    return {
        table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ("hotels", "trips", "users", "bookings")
    }


def test_initialize_database_seeds_all_supplied_records(tmp_path: Path) -> None:
    database_path = tmp_path / "expedia.sqlite3"

    assert initialize_database(database_path, DATA_DIRECTORY) is True

    connection = connect_database(database_path)
    try:
        assert _counts(connection) == {
            "hotels": 8,
            "trips": 12,
            "users": 6,
            "bookings": 6,
        }
        assert connection.execute(
            "SELECT nightly_rate_cents FROM hotels WHERE hotel_id = 'H001'"
        ).fetchone()["nightly_rate_cents"] == 15000
        assert connection.execute(
            "SELECT status FROM bookings WHERE booking_id = 'B002'"
        ).fetchone()["status"] == "cancelled"
        assert connection.execute(
            "SELECT value FROM app_metadata WHERE key = 'seed_version'"
        ).fetchone()["value"] == "2"
        assert connection.execute(
            "SELECT last_value FROM id_counters WHERE entity = 'booking'"
        ).fetchone()["last_value"] == 6
        assert connection.execute(
            "SELECT last_value FROM id_counters WHERE entity = 'user'"
        ).fetchone()["last_value"] == 6
        user = connection.execute(
            "SELECT username, password, email FROM users WHERE user_id = 'U001'"
        ).fetchone()
        assert dict(user) == {
            "username": "demo_u001",
            "password": "demo-pass-u001",
            "email": "demo_u001@example.test",
        }
    finally:
        connection.close()


def test_reinitialization_preserves_changes_and_does_not_reseed(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "expedia.sqlite3"
    initialize_database(database_path, DATA_DIRECTORY)

    connection = connect_database(database_path)
    try:
        connection.execute(
            "UPDATE bookings SET status = 'cancelled' WHERE booking_id = 'B001'"
        )
        connection.execute("DELETE FROM bookings WHERE booking_id = 'B006'")
        booking_id = allocate_booking_id(connection)
        connection.execute(
            """
            INSERT INTO bookings (
                booking_id, user_id, trip_id, booked_on, status
            ) VALUES (?, 'U006', 'T001', '2026-09-17', 'confirmed')
            """,
            (booking_id,),
        )
        connection.commit()
    finally:
        connection.close()

    assert booking_id == "B007"
    assert initialize_database(database_path, DATA_DIRECTORY) is False

    reopened = connect_database(database_path)
    try:
        assert _counts(reopened)["bookings"] == 6
        assert reopened.execute(
            "SELECT status FROM bookings WHERE booking_id = 'B001'"
        ).fetchone()["status"] == "cancelled"
        assert reopened.execute(
            "SELECT 1 FROM bookings WHERE booking_id = 'B006'"
        ).fetchone() is None
        assert reopened.execute(
            "SELECT user_id FROM bookings WHERE booking_id = 'B007'"
        ).fetchone()["user_id"] == "U006"
    finally:
        reopened.close()


def test_booking_ids_are_not_reused_after_delete(tmp_path: Path) -> None:
    database_path = tmp_path / "expedia.sqlite3"
    initialize_database(database_path, DATA_DIRECTORY)

    connection = connect_database(database_path)
    try:
        first_id = allocate_booking_id(connection)
        connection.execute(
            """
            INSERT INTO bookings (
                booking_id, user_id, trip_id, booked_on, status
            ) VALUES (?, 'U006', 'T001', '2026-09-17', 'confirmed')
            """,
            (first_id,),
        )
        connection.execute("DELETE FROM bookings WHERE booking_id = ?", (first_id,))
        second_id = allocate_booking_id(connection)
        connection.commit()
    finally:
        connection.close()

    assert first_id == "B007"
    assert second_id == "B008"


def test_user_ids_are_allocated_monotonically(tmp_path: Path) -> None:
    database_path = tmp_path / "expedia.sqlite3"
    initialize_database(database_path, DATA_DIRECTORY)

    connection = connect_database(database_path)
    try:
        first_id = allocate_user_id(connection)
        second_id = allocate_user_id(connection)
        connection.commit()
    finally:
        connection.close()

    assert first_id == "U007"
    assert second_id == "U008"


def test_schema_v1_migration_preserves_users_bookings_and_ids(tmp_path: Path) -> None:
    database_path = tmp_path / "expedia.sqlite3"
    connection = connect_database(database_path)
    try:
        connection.executescript(
            """
            CREATE TABLE app_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            INSERT INTO app_metadata VALUES ('schema_version', '1');
            INSERT INTO app_metadata VALUES ('seed_version', '1');
            CREATE TABLE users (
                user_id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL
            );
            CREATE TABLE hotels (
                hotel_id TEXT PRIMARY KEY,
                hotel_name TEXT NOT NULL,
                city TEXT NOT NULL,
                state TEXT NOT NULL,
                nightly_rate_cents INTEGER NOT NULL
            );
            CREATE TABLE trips (
                trip_id TEXT PRIMARY KEY,
                hotel_id TEXT NOT NULL REFERENCES hotels(hotel_id),
                trip_name TEXT NOT NULL,
                check_in TEXT NOT NULL,
                check_out TEXT NOT NULL
            );
            CREATE TABLE bookings (
                booking_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(user_id),
                trip_id TEXT NOT NULL REFERENCES trips(trip_id),
                booked_on TEXT NOT NULL,
                status TEXT NOT NULL
            );
            CREATE TABLE id_counters (
                entity TEXT PRIMARY KEY,
                last_value INTEGER NOT NULL
            );
            INSERT INTO users VALUES ('U042', 'Preserved Traveler');
            INSERT INTO hotels VALUES ('H001', 'Hotel', 'City', 'PA', 10000);
            INSERT INTO trips VALUES (
                'T001', 'H001', 'Trip', '2026-09-18', '2026-09-20'
            );
            INSERT INTO bookings VALUES (
                'B001', 'U042', 'T001', '2026-09-01', 'confirmed'
            );
            INSERT INTO id_counters VALUES ('booking', 1);
            """
        )
    finally:
        connection.close()

    assert initialize_database(database_path, DATA_DIRECTORY) is False

    migrated = connect_database(database_path)
    try:
        user = migrated.execute(
            "SELECT * FROM users WHERE user_id = 'U042'"
        ).fetchone()
        assert user["display_name"] == "Preserved Traveler"
        assert user["username"] == "demo_u042"
        assert user["password"] == "demo-pass-u042"
        assert migrated.execute(
            "SELECT user_id FROM bookings WHERE booking_id = 'B001'"
        ).fetchone()["user_id"] == "U042"
        assert allocate_user_id(migrated) == "U043"
        assert migrated.execute("PRAGMA foreign_key_check").fetchall() == []
        versions = dict(
            migrated.execute("SELECT key, value FROM app_metadata").fetchall()
        )
        assert versions["schema_version"] == "2"
        assert versions["seed_version"] == "2"
    finally:
        migrated.rollback()
        migrated.close()


def test_connections_enforce_foreign_keys(tmp_path: Path) -> None:
    database_path = tmp_path / "expedia.sqlite3"
    initialize_database(database_path, DATA_DIRECTORY)

    connection = connect_database(database_path)
    try:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO bookings (
                    booking_id, user_id, trip_id, booked_on, status
                ) VALUES ('B999', 'U999', 'T001', '2026-09-17', 'confirmed')
                """
            )
    finally:
        connection.rollback()
        connection.close()


def test_invalid_seed_data_writes_no_domain_rows(tmp_path: Path) -> None:
    seed_directory = tmp_path / "seed"
    seed_directory.mkdir()
    for filename in ("hotels.csv", "trips.csv", "users.csv", "bookings.csv"):
        shutil.copyfile(DATA_DIRECTORY / filename, seed_directory / filename)

    bookings_path = seed_directory / "bookings.csv"
    bookings_path.write_text(
        "booking_id,user_id,trip_id,booked_on,status\n"
        "B001,U999,T001,2026-09-01,confirmed\n",
        encoding="utf-8",
    )
    database_path = tmp_path / "expedia.sqlite3"

    with pytest.raises(SeedDataError, match="unknown user_id U999"):
        initialize_database(database_path, seed_directory)

    connection = connect_database(database_path)
    try:
        assert _counts(connection) == {
            "hotels": 0,
            "trips": 0,
            "users": 0,
            "bookings": 0,
        }
        assert connection.execute(
            "SELECT 1 FROM app_metadata WHERE key = 'seed_version'"
        ).fetchone() is None
    finally:
        connection.close()


def test_unmarked_partial_database_is_not_merged(tmp_path: Path) -> None:
    database_path = tmp_path / "expedia.sqlite3"
    connection = connect_database(database_path)
    try:
        create_schema(connection)
        connection.execute(
            """
            INSERT INTO hotels (
                hotel_id, hotel_name, city, state, nightly_rate_cents
            ) VALUES ('H999', 'Partial Hotel', 'Boston', 'MA', 10000)
            """
        )
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(SeedStateError, match="unmarked existing data"):
        initialize_database(database_path, DATA_DIRECTORY)

    reopened = connect_database(database_path)
    try:
        assert _counts(reopened) == {
            "hotels": 1,
            "trips": 0,
            "users": 0,
            "bookings": 0,
        }
        assert reopened.execute(
            "SELECT hotel_name FROM hotels WHERE hotel_id = 'H999'"
        ).fetchone()["hotel_name"] == "Partial Hotel"
    finally:
        reopened.close()


def test_unsupported_schema_version_is_rejected_without_creating_tables(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "expedia.sqlite3"
    connection = sqlite3.connect(database_path)
    try:
        connection.execute(
            "CREATE TABLE app_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO app_metadata VALUES ('schema_version', '999')"
        )
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(DatabaseVersionError, match="schema version: 999"):
        initialize_database(database_path, DATA_DIRECTORY)

    reopened = sqlite3.connect(database_path)
    try:
        assert reopened.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'hotels'"
        ).fetchone() is None
    finally:
        reopened.close()


def test_unsupported_seed_version_is_rejected_without_reimporting(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "expedia.sqlite3"
    initialize_database(database_path, DATA_DIRECTORY)
    connection = connect_database(database_path)
    try:
        connection.execute(
            "UPDATE app_metadata SET value = '999' WHERE key = 'seed_version'"
        )
        connection.execute("DELETE FROM bookings WHERE booking_id = 'B006'")
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(SeedStateError, match="seed version: 999"):
        initialize_database(database_path, DATA_DIRECTORY)

    reopened = connect_database(database_path)
    try:
        assert _counts(reopened)["bookings"] == 5
        assert reopened.execute(
            "SELECT 1 FROM bookings WHERE booking_id = 'B006'"
        ).fetchone() is None
    finally:
        reopened.close()
