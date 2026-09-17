import sqlite3
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path

import pytest

from backend.app.database import connect_database, initialize_database
from backend.app.search import search_hotel_stays

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
