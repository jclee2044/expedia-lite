"""Framework-free SQLite user lookup and booking CRUD logic."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal, cast

from backend.app.database import allocate_booking_id

BookingStatus = Literal["confirmed", "cancelled"]
VALID_BOOKING_STATUSES = {"confirmed", "cancelled"}


class RecordNotFoundError(LookupError):
    """Raised when a requested user, trip, or booking does not exist."""

    def __init__(self, resource: str, identifier: str) -> None:
        self.resource = resource
        self.identifier = identifier
        super().__init__(f"{resource.capitalize()} {identifier} was not found.")


class BookingValidationError(ValueError):
    """Raised when a booking operation contains an unsupported value."""


@dataclass(frozen=True)
class User:
    user_id: str
    display_name: str


@dataclass(frozen=True)
class BookingDetail:
    booking_id: str
    user_id: str
    display_name: str
    trip_id: str
    trip_name: str
    hotel_id: str
    hotel_name: str
    city: str
    state: str
    check_in: date
    check_out: date
    nights: int
    nightly_rate_usd: Decimal
    stay_price_usd: Decimal
    booked_on: date
    status: BookingStatus


@dataclass(frozen=True)
class BookingHistory:
    user: User
    booking_count: int
    bookings: list[BookingDetail]


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
    h.nightly_rate_cents,
    t.check_in,
    t.check_out,
    b.booked_on,
    b.status
FROM bookings AS b
JOIN users AS u ON u.user_id = b.user_id
JOIN trips AS t ON t.trip_id = b.trip_id
JOIN hotels AS h ON h.hotel_id = t.hotel_id
"""


def _booking_from_row(row: sqlite3.Row) -> BookingDetail:
    check_in = date.fromisoformat(row["check_in"])
    check_out = date.fromisoformat(row["check_out"])
    nights = (check_out - check_in).days
    nightly_rate = Decimal(row["nightly_rate_cents"]) / Decimal(100)
    return BookingDetail(
        booking_id=row["booking_id"],
        user_id=row["user_id"],
        display_name=row["display_name"],
        trip_id=row["trip_id"],
        trip_name=row["trip_name"],
        hotel_id=row["hotel_id"],
        hotel_name=row["hotel_name"],
        city=row["city"],
        state=row["state"],
        check_in=check_in,
        check_out=check_out,
        nights=nights,
        nightly_rate_usd=nightly_rate,
        stay_price_usd=nightly_rate * nights,
        booked_on=date.fromisoformat(row["booked_on"]),
        status=cast(BookingStatus, row["status"]),
    )


def list_users(connection: sqlite3.Connection) -> list[User]:
    """Return all synthetic travelers in stable ID order."""
    rows = connection.execute(
        "SELECT user_id, display_name FROM users ORDER BY user_id"
    ).fetchall()
    return [User(user_id=row["user_id"], display_name=row["display_name"]) for row in rows]


def get_user(connection: sqlite3.Connection, user_id: str) -> User:
    """Return one user or raise a domain not-found error."""
    row = connection.execute(
        "SELECT user_id, display_name FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()
    if row is None:
        raise RecordNotFoundError("user", user_id)
    return User(user_id=row["user_id"], display_name=row["display_name"])


def _require_trip(connection: sqlite3.Connection, trip_id: str) -> None:
    row = connection.execute(
        "SELECT 1 FROM trips WHERE trip_id = ?", (trip_id,)
    ).fetchone()
    if row is None:
        raise RecordNotFoundError("trip", trip_id)


def get_booking(connection: sqlite3.Connection, booking_id: str) -> BookingDetail:
    """Return one booking joined to its user, trip, and hotel."""
    row = connection.execute(
        BOOKING_SELECT + " WHERE b.booking_id = ?", (booking_id,)
    ).fetchone()
    if row is None:
        raise RecordNotFoundError("booking", booking_id)
    return _booking_from_row(row)


def list_user_bookings(
    connection: sqlite3.Connection,
    user_id: str,
) -> BookingHistory:
    """Return one user's joined booking history, including an empty history."""
    user = get_user(connection, user_id)
    rows = connection.execute(
        BOOKING_SELECT
        + " WHERE b.user_id = ? ORDER BY b.booked_on DESC, b.booking_id DESC",
        (user_id,),
    ).fetchall()
    bookings = [_booking_from_row(row) for row in rows]
    return BookingHistory(
        user=user,
        booking_count=len(bookings),
        bookings=bookings,
    )


def create_booking(
    connection: sqlite3.Connection,
    user_id: str,
    trip_id: str,
    booked_on: date | None = None,
) -> BookingDetail:
    """Create a confirmed booking and commit its ID and row atomically."""
    booking_date = booked_on or date.today()
    try:
        connection.execute("BEGIN IMMEDIATE")
        get_user(connection, user_id)
        _require_trip(connection, trip_id)
        booking_id = allocate_booking_id(connection)
        connection.execute(
            """
            INSERT INTO bookings (
                booking_id, user_id, trip_id, booked_on, status
            ) VALUES (?, ?, ?, ?, 'confirmed')
            """,
            (booking_id, user_id, trip_id, booking_date.isoformat()),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    return get_booking(connection, booking_id)


def update_booking_status(
    connection: sqlite3.Connection,
    booking_id: str,
    status: str,
) -> BookingDetail:
    """Update a booking's status while preserving the booking record."""
    if status not in VALID_BOOKING_STATUSES:
        raise BookingValidationError(f"Unsupported booking status: {status}")

    try:
        connection.execute("BEGIN IMMEDIATE")
        cursor = connection.execute(
            "UPDATE bookings SET status = ? WHERE booking_id = ?",
            (status, booking_id),
        )
        if cursor.rowcount == 0:
            raise RecordNotFoundError("booking", booking_id)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    return get_booking(connection, booking_id)


def delete_booking(connection: sqlite3.Connection, booking_id: str) -> None:
    """Permanently remove one booking."""
    try:
        connection.execute("BEGIN IMMEDIATE")
        cursor = connection.execute(
            "DELETE FROM bookings WHERE booking_id = ?", (booking_id,)
        )
        if cursor.rowcount == 0:
            raise RecordNotFoundError("booking", booking_id)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
