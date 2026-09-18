"""User lookup and booking-history business logic."""

from __future__ import annotations

import sqlite3

from backend.controllers.bookings import booking_from_row
from backend.controllers.database import fetch_user, fetch_user_bookings, fetch_users
from backend.controllers.errors import RecordNotFoundError
from backend.models import AccountProfile, BookingHistory


def account_profile_from_row(row: sqlite3.Row) -> AccountProfile:
    """Convert a database row to a password-free account projection."""
    return AccountProfile(
        user_id=row["user_id"],
        display_name=row["display_name"],
        username=row["username"],
        email=row["email"],
    )


def list_users(connection: sqlite3.Connection) -> list[AccountProfile]:
    """Return all synthetic travelers in stable ID order."""
    return [
        account_profile_from_row(row)
        for row in fetch_users(connection)
    ]


def get_user(connection: sqlite3.Connection, user_id: str) -> AccountProfile:
    """Return one user or raise a domain not-found error."""
    row = fetch_user(connection, user_id)
    if row is None:
        raise RecordNotFoundError("user", user_id)
    return account_profile_from_row(row)


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
