from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from backend.models import SearchHistory
from backend.models.pricing import (
    application_day_utc_bounds,
    calculate_nights,
    calculate_price_quote,
    count_matching_searches,
    normalize_search_query,
    pricing_context,
)


def test_calculate_nights_is_domain_logic() -> None:
    assert calculate_nights(date(2026, 9, 18), date(2026, 9, 20)) == 2

    with pytest.raises(ValueError, match="at least one night"):
        calculate_nights(date(2026, 9, 20), date(2026, 9, 20))


def _history(
    search_id: int,
    user_id: str,
    query: str,
    timestamp: str,
) -> SearchHistory:
    return SearchHistory(
        search_id=search_id,
        user_id=user_id,
        query=query,
        searched_at=datetime.fromisoformat(timestamp),
    )


def test_query_normalization_ignores_case_and_surrounding_whitespace() -> None:
    assert normalize_search_query("  VaLlEy  ") == "valley"
    assert normalize_search_query("Valley  Trail") == "valley  trail"


def test_application_day_bounds_follow_new_york_across_dst() -> None:
    winter_start, winter_end = application_day_utc_bounds(
        datetime(2026, 1, 15, 12, tzinfo=timezone.utc)
    )
    summer_start, summer_end = application_day_utc_bounds(
        datetime(2026, 7, 15, 12, tzinfo=timezone.utc)
    )

    assert winter_start.isoformat() == "2026-01-15T05:00:00+00:00"
    assert winter_end.isoformat() == "2026-01-16T05:00:00+00:00"
    assert summer_start.isoformat() == "2026-07-15T04:00:00+00:00"
    assert summer_end.isoformat() == "2026-07-16T04:00:00+00:00"


def test_frequency_is_scoped_by_user_query_and_local_calendar_day() -> None:
    history = [
        _history(1, "U001", "valley", "2026-09-18T04:00:00+00:00"),
        _history(2, "U001", "VALLEY", "2026-09-18T12:00:00+00:00"),
        _history(3, "U001", "trail", "2026-09-18T12:00:00+00:00"),
        _history(4, "U002", "valley", "2026-09-18T12:00:00+00:00"),
        _history(5, "U001", "valley", "2026-09-19T04:01:00+00:00"),
    ]

    count = count_matching_searches(
        history,
        "U001",
        "  Valley ",
        datetime.fromisoformat("2026-09-18T20:00:00+00:00"),
    )

    assert count == 2


@pytest.mark.parametrize(
    ("count", "expected_multiplier", "expected_rate"),
    [
        (1, Decimal("1.00"), Decimal("100.00")),
        (2, Decimal("1.00"), Decimal("100.00")),
        (3, Decimal("1.00"), Decimal("100.00")),
        (4, Decimal("1.20"), Decimal("120.00")),
        (12, Decimal("1.20"), Decimal("120.00")),
    ],
)
def test_fourth_and_later_searches_apply_one_non_compounding_increase(
    count: int,
    expected_multiplier: Decimal,
    expected_rate: Decimal,
) -> None:
    pricing = pricing_context(count)
    quote = calculate_price_quote(10000, 2, pricing)

    assert pricing.multiplier == expected_multiplier
    assert quote.base_nightly_rate_usd == Decimal("100.00")
    assert quote.nightly_rate_usd == expected_rate
    assert quote.stay_price_usd == expected_rate * 2


def test_anonymous_pricing_uses_base_rate_and_no_count() -> None:
    pricing = pricing_context(None)
    quote = calculate_price_quote(10000, 2, pricing)

    assert pricing.daily_search_count is None
    assert pricing.adjustment_applied is False
    assert quote.nightly_rate_usd == Decimal("100.00")


def test_price_rounding_is_half_up_to_one_cent() -> None:
    quote = calculate_price_quote(999, 1, pricing_context(4))

    assert quote.base_nightly_rate_usd == Decimal("9.99")
    assert quote.nightly_rate_usd == Decimal("11.99")


def test_naive_timestamps_are_rejected() -> None:
    with pytest.raises(ValueError, match="time zone"):
        application_day_utc_bounds(datetime(2026, 9, 18, 12))
