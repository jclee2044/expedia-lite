"""Booking CRUD business logic."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import cast

from backend.controllers.database import (
    allocate_booking_id,
    booking_belongs_to_user,
    delete_booking_row,
    fetch_booking,
    fetch_hotel_stays,
    fetch_user,
    fetch_user_search_history_between,
    insert_booking,
    trip_exists,
    update_booking_status_row,
)
from backend.controllers.errors import BookingValidationError, RecordNotFoundError
from backend.controllers.pricing import build_priced_stay
from backend.controllers.urgency import measure_search_frequency
from backend.models import BookingDetail, BookingStatus
from backend.models.pricing import (
    application_day_utc_bounds,
    normalize_search_query,
    pricing_context,
    require_aware_datetime,
)

VALID_BOOKING_STATUSES = {"confirmed", "cancelled"}


def booking_from_row(row: sqlite3.Row) -> BookingDetail:
    """Convert a joined SQLite row to a booking read model."""
    check_in = date.fromisoformat(row["check_in"])
    check_out = date.fromisoformat(row["check_out"])
    nights = (check_out - check_in).days
    nightly_rate = Decimal(row["quoted_nightly_rate_cents"]) / Decimal(100)
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


def get_booking(
    connection: sqlite3.Connection,
    booking_id: str,
    user_id: str | None = None,
) -> BookingDetail:
    """Return one booking joined to its user, trip, and hotel."""
    row = fetch_booking(connection, booking_id)
    if row is None:
        raise RecordNotFoundError("booking", booking_id)
    if user_id is not None and row["user_id"] != user_id:
        raise RecordNotFoundError("booking", booking_id)
    return booking_from_row(row)


def create_booking(
    connection: sqlite3.Connection,
    user_id: str,
    trip_id: str,
    booked_on: date | None = None,
    search_query: str | None = None,
    searched_at: datetime | None = None,
) -> BookingDetail:
    """Create a confirmed booking with a stable, server-derived price quote."""
    booking_date = booked_on or date.today()
    try:
        connection.execute("BEGIN IMMEDIATE")
        if fetch_user(connection, user_id) is None:
            raise RecordNotFoundError("user", user_id)
        if not trip_exists(connection, trip_id):
            raise RecordNotFoundError("trip", trip_id)

        stay_rows = fetch_hotel_stays(connection, search_query or "")
        stay_row = next((row for row in stay_rows if row["trip_id"] == trip_id), None)
        if stay_row is None:
            raise BookingValidationError(
                "The selected stay does not match the current hotel search."
            )

        daily_search_count: int | None = None
        if search_query is not None:
            normalized_query = normalize_search_query(search_query)
            if not normalized_query:
                raise BookingValidationError("Search again before booking this stay.")
            current_time = require_aware_datetime(
                searched_at or datetime.now(timezone.utc)
            )
            day_start, day_end = application_day_utc_bounds(current_time)
            history_rows = fetch_user_search_history_between(
                connection, user_id, day_start, day_end
            )
            daily_search_count = measure_search_frequency(
                history_rows, user_id, normalized_query, current_time
            )
            if daily_search_count == 0:
                raise BookingValidationError("Search again before booking this stay.")

        priced_stay = build_priced_stay(
            stay_row, pricing_context(daily_search_count)
        )
        quoted_nightly_rate_cents = int(
            priced_stay.nightly_rate_usd * Decimal(100)
        )
        booking_id = allocate_booking_id(connection)
        insert_booking(
            connection,
            booking_id,
            user_id,
            trip_id,
            booking_date.isoformat(),
            quoted_nightly_rate_cents,
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
    user_id: str | None = None,
) -> BookingDetail:
    """Update a booking's status while preserving the booking record."""
    if status not in VALID_BOOKING_STATUSES:
        raise BookingValidationError(f"Unsupported booking status: {status}")

    try:
        connection.execute("BEGIN IMMEDIATE")
        if user_id is not None and not booking_belongs_to_user(
            connection, booking_id, user_id
        ):
            raise RecordNotFoundError("booking", booking_id)
        if not update_booking_status_row(connection, booking_id, status):
            raise RecordNotFoundError("booking", booking_id)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    return get_booking(connection, booking_id)


def delete_booking(
    connection: sqlite3.Connection,
    booking_id: str,
    user_id: str | None = None,
) -> None:
    """Permanently remove one booking."""
    try:
        connection.execute("BEGIN IMMEDIATE")
        if user_id is not None and not booking_belongs_to_user(
            connection, booking_id, user_id
        ):
            raise RecordNotFoundError("booking", booking_id)
        if not delete_booking_row(connection, booking_id):
            raise RecordNotFoundError("booking", booking_id)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
