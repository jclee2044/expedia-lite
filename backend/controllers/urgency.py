"""Coordinate persisted search history with pure urgency calculations."""

from __future__ import annotations

import sqlite3
from datetime import datetime

from backend.models import SearchHistory
from backend.models.pricing import count_matching_searches


def history_from_rows(rows: list[sqlite3.Row]) -> list[SearchHistory]:
    """Translate raw persistence rows into domain history records."""
    return [
        SearchHistory(
            search_id=row["search_id"],
            user_id=row["user_id"],
            query=row["query"],
            searched_at=datetime.fromisoformat(row["searched_at_utc"]),
        )
        for row in rows
    ]


def measure_search_frequency(
    rows: list[sqlite3.Row],
    user_id: str,
    query: str,
    current_time: datetime,
) -> int:
    """Measure same-user, same-query frequency through the domain model."""
    return count_matching_searches(
        history_from_rows(rows), user_id, query, current_time
    )
