"""SQLite representation of Expedia Lite models and relationships."""

SCHEMA_VERSION = "7"

CHAT_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS chat_conversations (
    conversation_id TEXT PRIMARY KEY,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_messages (
    message_id INTEGER PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    turn_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL CHECK (length(trim(content)) > 0),
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (conversation_id) REFERENCES chat_conversations(conversation_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS chat_messages_conversation_idx
ON chat_messages (conversation_id, message_id);

CREATE TABLE IF NOT EXISTS chat_retrieval_stages (
    stage_id INTEGER PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    turn_id TEXT NOT NULL,
    stage TEXT NOT NULL CHECK (stage IN ('proposal', 'execution', 'result', 'error')),
    detail_json TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (conversation_id) REFERENCES chat_conversations(conversation_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS chat_retrieval_stages_conversation_idx
ON chat_retrieval_stages (conversation_id, stage_id);
"""

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

SAVED_HOTELS_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS saved_hotels (
    hotel_id TEXT PRIMARY KEY NOT NULL CHECK (length(trim(hotel_id)) > 0),
    name TEXT,
    address TEXT,
    latitude REAL NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude REAL NOT NULL CHECK (longitude BETWEEN -180 AND 180)
);

CREATE TABLE IF NOT EXISTS demo_hotel_nights (
    hotel_id TEXT NOT NULL,
    stay_date TEXT NOT NULL CHECK (
        length(stay_date) = 10
        AND stay_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
        AND COALESCE(date(stay_date, '+0 days') = stay_date, 0)
    ),
    nightly_rate_cents INTEGER NOT NULL DEFAULT 10000
        CHECK (typeof(nightly_rate_cents) = 'integer' AND nightly_rate_cents >= 0),
    rooms_available INTEGER NOT NULL DEFAULT 20
        CHECK (typeof(rooms_available) = 'integer' AND rooms_available >= 0),
    PRIMARY KEY (hotel_id, stay_date),
    FOREIGN KEY (hotel_id) REFERENCES saved_hotels(hotel_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT
);
"""

SAVED_HOTEL_ZIPS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS saved_hotel_zips (
    hotel_id TEXT NOT NULL,
    postcode TEXT NOT NULL CHECK (
        length(postcode) = 5 AND postcode GLOB '[0-9][0-9][0-9][0-9][0-9]'
    ),
    country_code TEXT NOT NULL CHECK (country_code = 'us'),
    latitude REAL NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude REAL NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    locality TEXT,
    PRIMARY KEY (hotel_id, postcode),
    FOREIGN KEY (hotel_id) REFERENCES saved_hotels(hotel_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT
);
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
    quoted_nightly_rate_cents INTEGER NOT NULL
        CHECK (quoted_nightly_rate_cents >= 0),
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
""" + SAVED_HOTELS_TABLES_SQL + SAVED_HOTEL_ZIPS_TABLE_SQL + CHAT_TABLES_SQL
