import sqlite3
from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest

from backend.app.bookings import (
    BookingValidationError,
    RecordNotFoundError,
    create_booking,
    delete_booking,
    get_booking,
    list_user_bookings,
    list_users,
    update_booking_status,
)
from backend.app.database import connect_database, initialize_database

DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"


@pytest.fixture
def connection(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    database_path = tmp_path / "expedia.sqlite3"
    initialize_database(database_path, DATA_DIRECTORY)
    database = connect_database(database_path)
    try:
        yield database
    finally:
        database.close()


def test_list_users_returns_all_seeded_users_in_id_order(
    connection: sqlite3.Connection,
) -> None:
    users = list_users(connection)

    assert [user.user_id for user in users] == [
        "U001",
        "U002",
        "U003",
        "U004",
        "U005",
        "U006",
    ]
    assert users[0].display_name == "Demo Traveler 1"


def test_seeded_and_empty_booking_histories(connection: sqlite3.Connection) -> None:
    first_history = list_user_bookings(connection, "U001")
    empty_history = list_user_bookings(connection, "U006")

    assert first_history.booking_count == 2
    assert [booking.booking_id for booking in first_history.bookings] == [
        "B002",
        "B001",
    ]
    assert first_history.bookings[1].hotel_id == "H001"
    assert first_history.bookings[1].nights == 2
    assert first_history.bookings[1].stay_price_usd == 300
    assert empty_history.user.display_name == "Demo Traveler 6"
    assert empty_history.booking_count == 0
    assert empty_history.bookings == []


def test_created_booking_survives_reopen(tmp_path: Path) -> None:
    database_path = tmp_path / "expedia.sqlite3"
    initialize_database(database_path, DATA_DIRECTORY)
    connection = connect_database(database_path)
    try:
        created = create_booking(
            connection,
            "U006",
            "T009",
            booked_on=date(2026, 9, 17),
        )
    finally:
        connection.close()

    reopened = connect_database(database_path)
    try:
        persisted = get_booking(reopened, created.booking_id)
    finally:
        reopened.close()

    assert created.booking_id == "B007"
    assert persisted == created
    assert persisted.status == "confirmed"
    assert persisted.booked_on == date(2026, 9, 17)
    assert persisted.hotel_name == "Harbor Lantern Hotel"
    assert persisted.stay_price_usd == 300


def test_missing_relations_do_not_consume_a_booking_id(
    connection: sqlite3.Connection,
) -> None:
    with pytest.raises(RecordNotFoundError, match="User U999"):
        create_booking(connection, "U999", "T001")
    with pytest.raises(RecordNotFoundError, match="Trip T999"):
        create_booking(connection, "U006", "T999")

    created = create_booking(connection, "U006", "T001")

    assert created.booking_id == "B007"


def test_cancellation_delete_and_next_id_have_distinct_behavior(
    connection: sqlite3.Connection,
) -> None:
    created = create_booking(connection, "U006", "T001")
    cancelled = update_booking_status(connection, created.booking_id, "cancelled")

    assert cancelled.status == "cancelled"
    assert list_user_bookings(connection, "U006").booking_count == 1

    delete_booking(connection, created.booking_id)

    with pytest.raises(RecordNotFoundError, match="Booking B007"):
        get_booking(connection, created.booking_id)
    assert list_user_bookings(connection, "U006").booking_count == 0

    next_booking = create_booking(connection, "U006", "T001")
    assert next_booking.booking_id == "B008"


def test_booking_operations_reject_missing_records_and_invalid_status(
    connection: sqlite3.Connection,
) -> None:
    with pytest.raises(RecordNotFoundError, match="User U999"):
        list_user_bookings(connection, "U999")
    with pytest.raises(RecordNotFoundError, match="Booking B999"):
        get_booking(connection, "B999")
    with pytest.raises(RecordNotFoundError, match="Booking B999"):
        update_booking_status(connection, "B999", "cancelled")
    with pytest.raises(RecordNotFoundError, match="Booking B999"):
        delete_booking(connection, "B999")
    with pytest.raises(BookingValidationError, match="Unsupported booking status"):
        update_booking_status(connection, "B001", "pending")
