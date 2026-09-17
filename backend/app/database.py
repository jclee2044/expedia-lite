"""SQLite connection and schema initialization for Expedia Lite."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from backend.app.seed import seed_database

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "backend" / "instance" / "expedia_lite.sqlite3"
DEFAULT_DATA_DIRECTORY = PROJECT_ROOT / "data"
SCHEMA_VERSION = "1"


class DatabaseVersionError(RuntimeError):
    """Raised when a database uses an unsupported schema version."""


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS app_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hotels (
    hotel_id TEXT PRIMARY KEY,
    hotel_name TEXT NOT NULL CHECK (length(trim(hotel_name)) > 0),
    city TEXT NOT NULL CHECK (length(trim(city)) > 0),
    state TEXT NOT NULL CHECK (length(trim(state)) > 0),
    nightly_rate_cents INTEGER NOT NULL CHECK (nightly_rate_cents >= 0)
);

CREATE TABLE IF NOT EXISTS trips (
    trip_id TEXT PRIMARY KEY,
    hotel_id TEXT NOT NULL,
    trip_name TEXT NOT NULL CHECK (length(trim(trip_name)) > 0),
    check_in TEXT NOT NULL
        CHECK (date(check_in) IS NOT NULL AND check_in = date(check_in)),
    check_out TEXT NOT NULL
        CHECK (date(check_out) IS NOT NULL AND check_out = date(check_out)),
    CHECK (check_out > check_in),
    FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL CHECK (length(trim(display_name)) > 0)
);

CREATE TABLE IF NOT EXISTS bookings (
    booking_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    trip_id TEXT NOT NULL,
    booked_on TEXT NOT NULL
        CHECK (date(booked_on) IS NOT NULL AND booked_on = date(booked_on)),
    status TEXT NOT NULL CHECK (status IN ('confirmed', 'cancelled')),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (trip_id) REFERENCES trips(trip_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS id_counters (
    entity TEXT PRIMARY KEY,
    last_value INTEGER NOT NULL CHECK (last_value >= 0)
);
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
    """Create schema version 1 or reject an incompatible existing database."""
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
        return


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
