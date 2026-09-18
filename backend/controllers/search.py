"""Hotel search business logic."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from backend.controllers.database import (
    fetch_hotel_stays,
    fetch_user_search_history_between,
    insert_search_history,
)
from backend.controllers.errors import SearchValidationError
from backend.controllers.pricing import build_priced_stay
from backend.controllers.urgency import measure_search_frequency
from backend.models import HotelSearch
from backend.models.pricing import (
    application_day_utc_bounds,
    normalize_search_query,
    pricing_context,
    require_aware_datetime,
)


def search_hotel_stays(
    query: str,
    connection: sqlite3.Connection,
    user_id: str | None = None,
    searched_at: datetime | None = None,
) -> HotelSearch:
    """Record an authenticated search and return model-priced stays."""
    display_query = query.strip()
    normalized_query = normalize_search_query(query)
    if not normalized_query:
        raise SearchValidationError("Enter a hotel name.")

    current_time = require_aware_datetime(searched_at or datetime.now(timezone.utc))
    daily_search_count: int | None = None

    if user_id is None:
        stay_rows = fetch_hotel_stays(connection, display_query)
    else:
        day_start, day_end = application_day_utc_bounds(current_time)
        try:
            connection.execute("BEGIN IMMEDIATE")
            insert_search_history(
                connection,
                user_id,
                normalized_query,
                current_time.astimezone(timezone.utc),
            )
            history_rows = fetch_user_search_history_between(
                connection, user_id, day_start, day_end
            )
            stay_rows = fetch_hotel_stays(connection, display_query)
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        daily_search_count = measure_search_frequency(
            history_rows, user_id, normalized_query, current_time
        )

    pricing = pricing_context(daily_search_count)
    results = [build_priced_stay(row, pricing) for row in stay_rows]

    return HotelSearch(
        query=display_query,
        hotel_count=len({result.hotel_id for result in results}),
        pricing=pricing,
        results=results,
    )
