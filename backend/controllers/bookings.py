"""Booking CRUD business logic."""

from __future__ import annotations

import sqlite3
from datetime import date
from decimal import Decimal
from typing import cast

from backend.controllers.database import (
    allocate_booking_id,
    delete_booking_row,
    fetch_booking,
    fetch_user,
    insert_booking,
    trip_exists,
    update_booking_status_row,
)
from backend.controllers.errors import BookingValidationError, RecordNotFoundError
from backend.models import BookingDetail, BookingStatus

VALID_BOOKING_STATUSES = {"confirmed", "cancelled"}


def booking_from_row(row: sqlite3.Row) -> BookingDetail:
    """Convert a joined SQLite row to a booking read model."""
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


def get_booking(connection: sqlite3.Connection, booking_id: str) -> BookingDetail:
    """Return one booking joined to its user, trip, and hotel."""
    row = fetch_booking(connection, booking_id)
    if row is None:
        raise RecordNotFoundError("booking", booking_id)
    return booking_from_row(row)


def create_booking(
    connection: sqlite3.Connection,
    user_id: str,
    trip_id: str,
    booked_on: date | None = None,
) -> BookingDetail:
    """Validate references and create a confirmed booking atomically."""
    booking_date = booked_on or date.today()
    try:
        connection.execute("BEGIN IMMEDIATE")
        if fetch_user(connection, user_id) is None:
            raise RecordNotFoundError("user", user_id)
        if not trip_exists(connection, trip_id):
            raise RecordNotFoundError("trip", trip_id)
        booking_id = allocate_booking_id(connection)
        insert_booking(
            connection,
            booking_id,
            user_id,
            trip_id,
            booking_date.isoformat(),
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
        if not update_booking_status_row(connection, booking_id, status):
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
        if not delete_booking_row(connection, booking_id):
            raise RecordNotFoundError("booking", booking_id)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
