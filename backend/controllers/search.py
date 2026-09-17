"""Hotel search business logic."""

from __future__ import annotations

import sqlite3
from datetime import date
from decimal import Decimal

from backend.controllers.database import fetch_hotel_stays
from backend.controllers.errors import SearchValidationError
from backend.models import HotelSearch, HotelStay


def search_hotel_stays(
    query: str,
    connection: sqlite3.Connection,
) -> HotelSearch:
    """Return stays whose hotel name contains the normalized query."""
    normalized_query = query.strip()
    if not normalized_query:
        raise SearchValidationError("Enter a hotel name.")

    results: list[HotelStay] = []
    for row in fetch_hotel_stays(connection, normalized_query):
        check_in = date.fromisoformat(row["check_in"])
        check_out = date.fromisoformat(row["check_out"])
        nights = (check_out - check_in).days
        nightly_rate = Decimal(row["nightly_rate_cents"]) / Decimal(100)
        results.append(
            HotelStay(
                hotel_id=row["hotel_id"],
                hotel_name=row["hotel_name"],
                city=row["city"],
                state=row["state"],
                trip_id=row["trip_id"],
                trip_name=row["trip_name"],
                check_in=check_in,
                check_out=check_out,
                nights=nights,
                nightly_rate_usd=nightly_rate,
                stay_price_usd=nightly_rate * nights,
            )
        )

    return HotelSearch(
        query=normalized_query,
        hotel_count=len({result.hotel_id for result in results}),
        results=results,
    )
