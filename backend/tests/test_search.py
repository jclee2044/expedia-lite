import sqlite3
from collections.abc import Iterator
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from backend.controllers.database import connect_database, initialize_database
from backend.controllers.search import search_hotel_stays

DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"


@pytest.fixture
def connection(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    database_path = tmp_path / "expedia.sqlite3"
    initialize_database(database_path, DATA_DIRECTORY)
    database = connect_database(database_path)
    try:
        yield database
    finally:
        database.close()


def test_search_joins_all_stays_for_matching_hotel(
    connection: sqlite3.Connection,
) -> None:
    search = search_hotel_stays("Harbor", connection)

    assert search.query == "Harbor"
    assert search.hotel_count == 1
    assert [stay.trip_id for stay in search.results] == ["T001", "T009"]
    assert {stay.hotel_id for stay in search.results} == {"H001"}
    assert {stay.hotel_name for stay in search.results} == {
        "Harbor Lantern Hotel"
    }
    assert search.pricing.daily_search_count is None
    assert search.pricing.adjustment_applied is False


def test_search_is_case_insensitive_partial_and_trims_whitespace(
    connection: sqlite3.Connection,
) -> None:
    search = search_hotel_stays("  lantern  ", connection)

    assert search.query == "lantern"
    assert search.hotel_count == 1
    assert len(search.results) == 2


def test_search_calculates_nights_and_stay_price(
    connection: sqlite3.Connection,
) -> None:
    search = search_hotel_stays("Maple Square", connection)

    first_stay = search.results[0]
    assert first_stay.trip_id == "T002"
    assert first_stay.nights == 3
    assert first_stay.nightly_rate_usd == Decimal("120")
    assert first_stay.stay_price_usd == Decimal("360")
    assert first_stay.base_nightly_rate_usd == Decimal("120")
    assert first_stay.base_stay_price_usd == Decimal("360")


def test_search_returns_empty_result_for_unknown_hotel(
    connection: sqlite3.Connection,
) -> None:
    search = search_hotel_stays("Not A Supplied Hotel", connection)

    assert search.hotel_count == 0
    assert search.results == []


def test_search_rejects_blank_query(connection: sqlite3.Connection) -> None:
    with pytest.raises(ValueError, match="Enter a hotel name"):
        search_hotel_stays("   ", connection)


@pytest.mark.parametrize(
    ("query", "hotel_count", "trip_ids"),
    [
        ("CAPITOL", 1, ["T007", "T012"]),
        (
            "hotel",
            5,
            ["T001", "T003", "T004", "T006", "T007", "T009", "T011", "T012"],
        ),
    ],
)
def test_search_matches_documented_screenshot_results(
    connection: sqlite3.Connection,
    query: str,
    hotel_count: int,
    trip_ids: list[str],
) -> None:
    search = search_hotel_stays(query, connection)

    assert search.hotel_count == hotel_count
    assert [stay.trip_id for stay in search.results] == trip_ids


def test_authenticated_fourth_matching_search_applies_once(
    connection: sqlite3.Connection,
) -> None:
    searched_at = datetime(2026, 9, 18, 14, 0, tzinfo=timezone.utc)
    searches = [
        search_hotel_stays(
            query, connection, user_id="U001", searched_at=searched_at
        )
        for query in ("Valley Trail", " valley trail ", "VALLEY TRAIL", "Valley Trail")
    ]

    assert [search.pricing.daily_search_count for search in searches] == [1, 2, 3, 4]
    assert [search.results[0].nightly_rate_usd for search in searches] == [
        Decimal("100.00"), Decimal("100.00"), Decimal("100.00"), Decimal("120.00")
    ]
    latest = searches[-1]
    for _ in range(8):
        latest = search_hotel_stays(
            "Valley Trail", connection, user_id="U001", searched_at=searched_at
        )
    assert latest.pricing.daily_search_count == 12
    assert latest.results[0].nightly_rate_usd == Decimal("120.00")
    stored_base = connection.execute(
        "SELECT nightly_rate_cents FROM hotels WHERE hotel_id = 'H008'"
    ).fetchone()
    assert stored_base["nightly_rate_cents"] == 10_000


def test_frequency_isolated_by_user_query_and_application_day(
    connection: sqlite3.Connection,
) -> None:
    day_one = datetime(2026, 9, 18, 14, 0, tzinfo=timezone.utc)
    day_two = datetime(2026, 9, 19, 14, 0, tzinfo=timezone.utc)
    for _ in range(4):
        search_hotel_stays(
            "Valley Trail", connection, user_id="U001", searched_at=day_one
        )

    isolated_searches = [
        search_hotel_stays(
            "Valley Trail", connection, user_id="U002", searched_at=day_one
        ),
        search_hotel_stays(
            "Valley", connection, user_id="U001", searched_at=day_one
        ),
        search_hotel_stays(
            "Valley Trail", connection, user_id="U001", searched_at=day_two
        ),
    ]
    for search in isolated_searches:
        assert search.pricing.daily_search_count == 1
        assert search.results[0].nightly_rate_usd == Decimal("100.00")


def test_authenticated_no_result_is_recorded_but_blank_is_not(
    connection: sqlite3.Connection,
) -> None:
    searched_at = datetime(2026, 9, 18, 14, 0, tzinfo=timezone.utc)
    search = search_hotel_stays(
        "No Such Hotel", connection, user_id="U001", searched_at=searched_at
    )
    assert search.results == []
    assert search.pricing.daily_search_count == 1

    with pytest.raises(ValueError, match="Enter a hotel name"):
        search_hotel_stays(
            "   ", connection, user_id="U001", searched_at=searched_at
        )
    count = connection.execute("SELECT COUNT(*) FROM search_history").fetchone()[0]
    assert count == 1
