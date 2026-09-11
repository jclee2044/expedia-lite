from decimal import Decimal
from pathlib import Path

import pytest

from backend.app.search import search_hotel_stays

DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"
HOTELS_PATH = DATA_DIRECTORY / "hotels.csv"
TRIPS_PATH = DATA_DIRECTORY / "trips.csv"


def test_search_joins_all_stays_for_matching_hotel() -> None:
    search = search_hotel_stays("Harbor", HOTELS_PATH, TRIPS_PATH)

    assert search.query == "Harbor"
    assert search.hotel_count == 1
    assert [stay.trip_id for stay in search.results] == ["T001", "T009"]
    assert {stay.hotel_id for stay in search.results} == {"H001"}
    assert {stay.hotel_name for stay in search.results} == {
        "Harbor Lantern Hotel"
    }


def test_search_is_case_insensitive_partial_and_trims_whitespace() -> None:
    search = search_hotel_stays("  lantern  ", HOTELS_PATH, TRIPS_PATH)

    assert search.query == "lantern"
    assert search.hotel_count == 1
    assert len(search.results) == 2


def test_search_calculates_nights_and_stay_price() -> None:
    search = search_hotel_stays("Maple Square", HOTELS_PATH, TRIPS_PATH)

    first_stay = search.results[0]
    assert first_stay.trip_id == "T002"
    assert first_stay.nights == 3
    assert first_stay.nightly_rate_usd == Decimal("120")
    assert first_stay.stay_price_usd == Decimal("360")


def test_search_returns_empty_result_for_unknown_hotel() -> None:
    search = search_hotel_stays("Not A Supplied Hotel", HOTELS_PATH, TRIPS_PATH)

    assert search.hotel_count == 0
    assert search.results == []


def test_search_rejects_blank_query() -> None:
    with pytest.raises(ValueError, match="Enter a hotel name"):
        search_hotel_stays("   ", HOTELS_PATH, TRIPS_PATH)
