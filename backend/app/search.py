"""Framework-free SQLite hotel search logic."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


class SearchValidationError(ValueError):
    """Raised when a hotel search query is not usable."""


@dataclass(frozen=True)
class HotelStay:
    hotel_id: str
    hotel_name: str
    city: str
    state: str
    trip_id: str
    trip_name: str
    check_in: date
    check_out: date
    nights: int
    nightly_rate_usd: Decimal
    stay_price_usd: Decimal


@dataclass(frozen=True)
class HotelSearch:
    query: str
    hotel_count: int
    results: list[HotelStay]


SEARCH_SQL = """
SELECT
    h.hotel_id,
    h.hotel_name,
    h.city,
    h.state,
    h.nightly_rate_cents,
    t.trip_id,
    t.trip_name,
    t.check_in,
    t.check_out
FROM hotels AS h
JOIN trips AS t ON t.hotel_id = h.hotel_id
WHERE instr(casefold(h.hotel_name), casefold(?)) > 0
ORDER BY t.trip_id
"""


def search_hotel_stays(
    query: str,
    connection: sqlite3.Connection,
) -> HotelSearch:
    """Return SQLite stays whose hotel name contains the normalized query."""
    normalized_query = query.strip()
    if not normalized_query:
        raise SearchValidationError("Enter a hotel name.")

    results: list[HotelStay] = []
    for row in connection.execute(SEARCH_SQL, (normalized_query,)):
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
