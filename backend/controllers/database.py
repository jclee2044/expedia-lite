"""SQLite connection, initialization, and data operations."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from backend.controllers.seed import seed_database
from backend.models.schema import (
    CHAT_TABLES_SQL,
    SCHEMA_SQL,
    SCHEMA_VERSION,
    SAVED_HOTEL_ZIPS_TABLE_SQL,
    SAVED_HOTELS_TABLES_SQL,
    SEARCH_HISTORY_TABLE_SQL,
    USERS_TABLE_SQL,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
# Runtime state is kept outside the application and controller packages.
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "backend" / "db" / "expedia_lite.sqlite3"
DEFAULT_DATA_DIRECTORY = PROJECT_ROOT / "data"


class DatabaseVersionError(RuntimeError):
    """Raised when a database uses an unsupported schema version."""


BOOKING_SELECT = """
SELECT
    b.booking_id,
    b.user_id,
    u.display_name,
    b.trip_id,
    t.trip_name,
    h.hotel_id,
    h.hotel_name,
    h.city,
    h.state,
    b.quoted_nightly_rate_cents,
    t.check_in,
    t.check_out,
    b.booked_on,
    b.status
FROM bookings AS b
JOIN users AS u ON u.user_id = b.user_id
JOIN trips AS t ON t.trip_id = b.trip_id
JOIN hotels AS h ON h.hotel_id = t.hotel_id
"""

SEARCH_SELECT = """
SELECT
    h.hotel_id,
    h.hotel_name,
    h.city,
    h.state,
    h.nightly_rate_cents,
    t.trip_id,
    t.trip_name,
    t.check_in,
    t.check_out
FROM hotels AS h
JOIN trips AS t ON t.hotel_id = h.hotel_id
WHERE instr(casefold(h.hotel_name), casefold(?)) > 0
ORDER BY t.trip_id
"""


def connect_database(database_path: Path) -> sqlite3.Connection:
    """Open a configured SQLite connection and enable relationship checks."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.create_function(
        "casefold",
        1,
        lambda value: value.casefold() if isinstance(value, str) else value,
        deterministic=True,
    )
    return connection


def create_schema(connection: sqlite3.Connection) -> None:
    """Create the current schema or migrate a supported existing database."""
    metadata_exists = connection.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table' AND name = 'app_metadata'
        """
    ).fetchone()
    version_row = None
    if metadata_exists is not None:
        version_row = connection.execute(
            "SELECT value FROM app_metadata WHERE key = 'schema_version'"
        ).fetchone()

    if version_row is not None and version_row["value"] == "1":
        _migrate_schema_v1_to_v2(connection)
        version_row = {"value": "2"}

    if version_row is not None and version_row["value"] == "2":
        _migrate_schema_v2_to_v3(connection)
        version_row = {"value": "3"}

    if version_row is not None and version_row["value"] == "3":
        _migrate_schema_v3_to_v4(connection)
        version_row = {"value": "4"}

    if version_row is not None and version_row["value"] == "4":
        _migrate_schema_v4_to_v5(connection)
        version_row = {"value": "5"}

    if version_row is not None and version_row["value"] == "5":
        _migrate_schema_v5_to_v6(connection)
        version_row = {"value": "6"}

    if version_row is not None and version_row["value"] == "6":
        _migrate_schema_v6_to_v7(connection)
        version_row = {"value": "7"}

    if version_row is not None and version_row["value"] != SCHEMA_VERSION:
        raise DatabaseVersionError(
            f"Unsupported database schema version: {version_row['value']}"
        )

    connection.executescript(SCHEMA_SQL)

    if version_row is None:
        connection.execute(
            "INSERT INTO app_metadata (key, value) VALUES ('schema_version', ?)",
            (SCHEMA_VERSION,),
        )
        connection.commit()


def _migrate_schema_v1_to_v2(connection: sqlite3.Connection) -> None:
    """Add account credentials while preserving every user ID and relationship."""
    seed_row = connection.execute(
        "SELECT value FROM app_metadata WHERE key = 'seed_version'"
    ).fetchone()
    if seed_row is not None and seed_row["value"] not in {"1", "2"}:
        raise DatabaseVersionError(
            f"Unsupported database seed version: {seed_row['value']}"
        )

    foreign_keys_enabled = connection.execute("PRAGMA foreign_keys").fetchone()[0]
    connection.execute("PRAGMA foreign_keys = OFF")
    try:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            USERS_TABLE_SQL.replace(
                "CREATE TABLE users", "CREATE TABLE users_v2", 1
            ).strip()
        )
        users = connection.execute(
            "SELECT user_id, display_name FROM users ORDER BY user_id"
        ).fetchall()
        connection.executemany(
            """
            INSERT INTO users_v2 (
                user_id, display_name, username, password, email
            ) VALUES (?, ?, ?, ?, NULL)
            """,
            [
                (
                    row["user_id"],
                    row["display_name"],
                    f"demo_{row['user_id'].lower()}",
                    f"demo-pass-{row['user_id'].lower()}",
                )
                for row in users
            ],
        )
        connection.execute("DROP TABLE users")
        connection.execute("ALTER TABLE users_v2 RENAME TO users")
        greatest_user_suffix = max(
            (int(row["user_id"][1:]) for row in users),
            default=0,
        )
        connection.execute(
            """
            INSERT INTO id_counters (entity, last_value)
            VALUES ('user', ?)
            ON CONFLICT(entity) DO UPDATE SET last_value = excluded.last_value
            """,
            (greatest_user_suffix,),
        )
        connection.execute(
            "UPDATE app_metadata SET value = ? WHERE key = 'schema_version'",
            ("2",),
        )
        if seed_row is not None:
            connection.execute(
                "UPDATE app_metadata SET value = '2' WHERE key = 'seed_version'"
            )
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise DatabaseVersionError(
                "Schema migration would break existing database relationships."
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.execute(
            f"PRAGMA foreign_keys = {1 if foreign_keys_enabled else 0}"
        )


def _migrate_schema_v2_to_v3(connection: sqlite3.Connection) -> None:
    """Add shared search history without changing existing domain records."""
    try:
        connection.execute("BEGIN IMMEDIATE")
        for statement in SEARCH_HISTORY_TABLE_SQL.split(";"):
            if statement.strip():
                connection.execute(statement)
        connection.execute(
            "UPDATE app_metadata SET value = ? WHERE key = 'schema_version'",
            ("3",),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def _migrate_schema_v3_to_v4(connection: sqlite3.Connection) -> None:
    """Snapshot each existing booking's hotel rate for stable history prices."""
    try:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            """
            ALTER TABLE bookings
            ADD COLUMN quoted_nightly_rate_cents INTEGER NOT NULL DEFAULT 0
                CHECK (quoted_nightly_rate_cents >= 0)
            """
        )
        connection.execute(
            """
            UPDATE bookings
            SET quoted_nightly_rate_cents = (
                SELECT h.nightly_rate_cents
                FROM trips AS t
                JOIN hotels AS h ON h.hotel_id = t.hotel_id
                WHERE t.trip_id = bookings.trip_id
            )
            """
        )
        connection.execute(
            "UPDATE app_metadata SET value = ? WHERE key = 'schema_version'",
            ("4",),
        )
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise DatabaseVersionError(
                "Schema migration would break existing database relationships."
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def _migrate_schema_v4_to_v5(connection: sqlite3.Connection) -> None:
    """Add provider hotel and fictional nightly inventory tables without data changes."""
    try:
        connection.execute("BEGIN IMMEDIATE")
        for statement in SAVED_HOTELS_TABLES_SQL.split(";"):
            if statement.strip():
                connection.execute(statement)
        connection.execute(
            "UPDATE app_metadata SET value = ? WHERE key = 'schema_version'",
            ("5",),
        )
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise DatabaseVersionError(
                "Schema migration would break existing database relationships."
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def _migrate_schema_v5_to_v6(connection: sqlite3.Connection) -> None:
    """Add ZIP associations without changing existing saved hotels or nights."""
    try:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(SAVED_HOTEL_ZIPS_TABLE_SQL.strip())
        connection.execute(
            "UPDATE app_metadata SET value = ? WHERE key = 'schema_version'",
            ("6",),
        )
        if connection.execute("PRAGMA foreign_key_check").fetchall():
            raise DatabaseVersionError(
                "Schema migration would break existing database relationships."
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def _migrate_schema_v6_to_v7(connection: sqlite3.Connection) -> None:
    """Add chat history and retrieval trace tables without changing hotel data."""
    try:
        connection.execute("BEGIN IMMEDIATE")
        for statement in CHAT_TABLES_SQL.split(";"):
            if statement.strip():
                connection.execute(statement)
        connection.execute(
            "UPDATE app_metadata SET value = ? WHERE key = 'schema_version'",
            (SCHEMA_VERSION,),
        )
        if connection.execute("PRAGMA foreign_key_check").fetchall():
            raise DatabaseVersionError(
                "Schema migration would break existing database relationships."
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def initialize_database(
    database_path: Path = DEFAULT_DATABASE_PATH,
    data_directory: Path = DEFAULT_DATA_DIRECTORY,
) -> bool:
    """Create the schema and seed a new database, returning whether it seeded."""
    connection = connect_database(database_path)
    try:
        create_schema(connection)
        return seed_database(connection, data_directory)
    finally:
        connection.close()


def allocate_booking_id(connection: sqlite3.Connection) -> str:
    """Advance the durable booking counter inside the caller's transaction."""
    row = connection.execute(
        """
        UPDATE id_counters
        SET last_value = last_value + 1
        WHERE entity = 'booking'
        RETURNING last_value
        """
    ).fetchone()
    if row is None:
        raise RuntimeError("The booking ID counter has not been initialized.")
    return f"B{row['last_value']:03d}"


def allocate_user_id(connection: sqlite3.Connection) -> str:
    """Advance the durable user counter inside the caller's transaction."""
    row = connection.execute(
        """
        UPDATE id_counters
        SET last_value = last_value + 1
        WHERE entity = 'user'
        RETURNING last_value
        """
    ).fetchone()
    if row is None:
        raise RuntimeError("The user ID counter has not been initialized.")
    return f"U{row['last_value']:03d}"


def fetch_users(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    """Read all users in stable ID order."""
    return connection.execute(
        """
        SELECT user_id, display_name, username, email
        FROM users
        ORDER BY user_id
        """
    ).fetchall()


def fetch_user(connection: sqlite3.Connection, user_id: str) -> sqlite3.Row | None:
    """Read one user row."""
    return connection.execute(
        """
        SELECT user_id, display_name, username, password, email
        FROM users
        WHERE user_id = ?
        """,
        (user_id,),
    ).fetchone()


def fetch_user_by_username(
    connection: sqlite3.Connection, username: str
) -> sqlite3.Row | None:
    """Read one account by its case-insensitive unique username."""
    return connection.execute(
        """
        SELECT user_id, display_name, username, password, email
        FROM users
        WHERE username = ? COLLATE NOCASE
        """,
        (username,),
    ).fetchone()


def insert_user(
    connection: sqlite3.Connection,
    user_id: str,
    display_name: str,
    username: str,
    password: str,
    email: str | None,
) -> None:
    """Insert one account inside the caller's transaction."""
    connection.execute(
        """
        INSERT INTO users (user_id, display_name, username, password, email)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, display_name, username, password, email),
    )


def booking_belongs_to_user(
    connection: sqlite3.Connection, booking_id: str, user_id: str
) -> bool:
    """Return whether one persisted booking belongs to the given account."""
    return (
        connection.execute(
            "SELECT 1 FROM bookings WHERE booking_id = ? AND user_id = ?",
            (booking_id, user_id),
        ).fetchone()
        is not None
    )


def trip_exists(connection: sqlite3.Connection, trip_id: str) -> bool:
    """Return whether a trip reference exists."""
    return (
        connection.execute(
            "SELECT 1 FROM trips WHERE trip_id = ?", (trip_id,)
        ).fetchone()
        is not None
    )


def fetch_booking(connection: sqlite3.Connection, booking_id: str) -> sqlite3.Row | None:
    """Read one booking joined to its related records."""
    return connection.execute(
        BOOKING_SELECT + " WHERE b.booking_id = ?", (booking_id,)
    ).fetchone()


def fetch_user_bookings(
    connection: sqlite3.Connection, user_id: str
) -> list[sqlite3.Row]:
    """Read one user's joined booking rows in history order."""
    return connection.execute(
        BOOKING_SELECT
        + " WHERE b.user_id = ? ORDER BY b.booked_on DESC, b.booking_id DESC",
        (user_id,),
    ).fetchall()


def fetch_hotel_stays(
    connection: sqlite3.Connection, query: str
) -> list[sqlite3.Row]:
    """Read stays whose hotel name contains the normalized query."""
    return connection.execute(SEARCH_SELECT, (query,)).fetchall()


def insert_search_history(
    connection: sqlite3.Connection,
    user_id: str,
    query: str,
    searched_at_utc: datetime,
) -> int:
    """Persist one normalized search inside the caller's transaction."""
    row = connection.execute(
        """
        INSERT INTO search_history (user_id, query, searched_at_utc)
        VALUES (?, ?, ?)
        RETURNING search_id
        """,
        (user_id, query, searched_at_utc.isoformat()),
    ).fetchone()
    if row is None:
        raise RuntimeError("The search history record was not created.")
    return int(row["search_id"])


def fetch_user_search_history_between(
    connection: sqlite3.Connection,
    user_id: str,
    start_utc: datetime,
    end_utc: datetime,
) -> list[sqlite3.Row]:
    """Read raw history rows for one user in a half-open UTC interval."""
    return connection.execute(
        """
        SELECT search_id, user_id, query, searched_at_utc
        FROM search_history
        WHERE user_id = ?
          AND searched_at_utc >= ?
          AND searched_at_utc < ?
        ORDER BY searched_at_utc, search_id
        """,
        (user_id, start_utc.isoformat(), end_utc.isoformat()),
    ).fetchall()


def insert_booking(
    connection: sqlite3.Connection,
    booking_id: str,
    user_id: str,
    trip_id: str,
    booked_on: str,
    quoted_nightly_rate_cents: int,
) -> None:
    """Insert one confirmed booking inside the caller's transaction."""
    connection.execute(
        """
        INSERT INTO bookings (
            booking_id, user_id, trip_id, booked_on,
            quoted_nightly_rate_cents, status
        ) VALUES (?, ?, ?, ?, ?, 'confirmed')
        """,
        (booking_id, user_id, trip_id, booked_on, quoted_nightly_rate_cents),
    )


def update_booking_status_row(
    connection: sqlite3.Connection, booking_id: str, status: str
) -> bool:
    """Update a booking status and report whether a row changed."""
    cursor = connection.execute(
        "UPDATE bookings SET status = ? WHERE booking_id = ?",
        (status, booking_id),
    )
    return cursor.rowcount > 0


def delete_booking_row(connection: sqlite3.Connection, booking_id: str) -> bool:
    """Delete a booking and report whether a row changed."""
    cursor = connection.execute(
        "DELETE FROM bookings WHERE booking_id = ?", (booking_id,)
    )
    return cursor.rowcount > 0
