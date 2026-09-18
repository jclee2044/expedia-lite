"""Build priced search results by delegating calculations to the model."""

from __future__ import annotations

import sqlite3
from datetime import date

from backend.models import HotelStay, SearchPricing
from backend.models.pricing import calculate_nights, calculate_price_quote


def build_priced_stay(row: sqlite3.Row, pricing: SearchPricing) -> HotelStay:
    """Translate one raw joined stay row into a model-calculated quote."""
    check_in = date.fromisoformat(row["check_in"])
    check_out = date.fromisoformat(row["check_out"])
    nights = calculate_nights(check_in, check_out)
    quote = calculate_price_quote(row["nightly_rate_cents"], nights, pricing)
    return HotelStay(
        hotel_id=row["hotel_id"],
        hotel_name=row["hotel_name"],
        city=row["city"],
        state=row["state"],
        trip_id=row["trip_id"],
        trip_name=row["trip_name"],
        check_in=check_in,
        check_out=check_out,
        nights=nights,
        base_nightly_rate_usd=quote.base_nightly_rate_usd,
        nightly_rate_usd=quote.nightly_rate_usd,
        base_stay_price_usd=quote.base_stay_price_usd,
        stay_price_usd=quote.stay_price_usd,
    )
