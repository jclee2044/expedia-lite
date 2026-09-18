"""SQLite representation of Expedia Lite models and relationships."""

SCHEMA_VERSION = "3"

USERS_TABLE_SQL = """
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL CHECK (length(trim(display_name)) > 0),
    username TEXT NOT NULL COLLATE NOCASE UNIQUE
        CHECK (length(trim(username)) BETWEEN 3 AND 32),
    password TEXT NOT NULL CHECK (length(password) BETWEEN 4 AND 72),
    email TEXT CHECK (
        email IS NULL OR (
            length(trim(email)) > 0
            AND instr(email, '@') > 1
            AND instr(substr(email, instr(email, '@') + 1), '.') > 1
        )
    )
);
"""

SEARCH_HISTORY_TABLE_SQL = """
CREATE TABLE search_history (
    search_id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    query TEXT NOT NULL CHECK (length(trim(query)) > 0),
    searched_at_utc TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE INDEX search_history_user_time_idx
ON search_history (user_id, searched_at_utc);
"""

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
    display_name TEXT NOT NULL CHECK (length(trim(display_name)) > 0),
    username TEXT NOT NULL COLLATE NOCASE UNIQUE
        CHECK (length(trim(username)) BETWEEN 3 AND 32),
    password TEXT NOT NULL CHECK (length(password) BETWEEN 4 AND 72),
    email TEXT CHECK (
        email IS NULL OR (
            length(trim(email)) > 0
            AND instr(email, '@') > 1
            AND instr(substr(email, instr(email, '@') + 1), '.') > 1
        )
    )
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

CREATE TABLE IF NOT EXISTS search_history (
    search_id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    query TEXT NOT NULL CHECK (length(trim(query)) > 0),
    searched_at_utc TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS search_history_user_time_idx
ON search_history (user_id, searched_at_utc);

CREATE TABLE IF NOT EXISTS id_counters (
    entity TEXT PRIMARY KEY,
    last_value INTEGER NOT NULL CHECK (last_value >= 0)
);
"""
