"""User lookup and booking-history business logic."""

from __future__ import annotations

import sqlite3

from backend.controllers.bookings import booking_from_row
from backend.controllers.database import fetch_user, fetch_user_bookings, fetch_users
from backend.controllers.errors import RecordNotFoundError
from backend.models import BookingHistory, User


def list_users(connection: sqlite3.Connection) -> list[User]:
    """Return all synthetic travelers in stable ID order."""
    return [
        User(user_id=row["user_id"], display_name=row["display_name"])
        for row in fetch_users(connection)
    ]


def get_user(connection: sqlite3.Connection, user_id: str) -> User:
    """Return one user or raise a domain not-found error."""
    row = fetch_user(connection, user_id)
    if row is None:
        raise RecordNotFoundError("user", user_id)
    return User(user_id=row["user_id"], display_name=row["display_name"])


def list_user_bookings(
    connection: sqlite3.Connection,
    user_id: str,
) -> BookingHistory:
    """Return one user's joined booking history, including an empty history."""
    user = get_user(connection, user_id)
    bookings = [
        booking_from_row(row) for row in fetch_user_bookings(connection, user_id)
    ]
    return BookingHistory(
        user=user,
        booking_count=len(bookings),
        bookings=bookings,
    )
