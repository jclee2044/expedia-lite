"""Pure domain calculations for search urgency and personalized pricing."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from zoneinfo import ZoneInfo

from backend.models.entities import PriceQuote, SearchHistory, SearchPricing

APPLICATION_TIME_ZONE_NAME = "America/New_York"
APPLICATION_TIME_ZONE = ZoneInfo(APPLICATION_TIME_ZONE_NAME)
BASE_MULTIPLIER = Decimal("1.00")
URGENCY_MULTIPLIER = Decimal("1.20")
URGENCY_THRESHOLD = 4
ONE_CENT = Decimal("0.01")


def calculate_nights(check_in: date, check_out: date) -> int:
    """Calculate and validate a stay's length in the domain model."""
    nights = (check_out - check_in).days
    if nights <= 0:
        raise ValueError("A stay must contain at least one night.")
    return nights


def normalize_search_query(query: str) -> str:
    """Normalize only surrounding whitespace and capitalization."""
    return query.strip().casefold()


def require_aware_datetime(value: datetime) -> datetime:
    """Reject ambiguous naive timestamps at the domain boundary."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Search timestamps must include a time zone.")
    return value


def application_day_utc_bounds(value: datetime) -> tuple[datetime, datetime]:
    """Return the UTC start/end instants for value's New York calendar day."""
    aware_value = require_aware_datetime(value)
    local_value = aware_value.astimezone(APPLICATION_TIME_ZONE)
    local_start = local_value.replace(hour=0, minute=0, second=0, microsecond=0)
    next_local_date = local_start.date().fromordinal(local_start.date().toordinal() + 1)
    local_end = datetime.combine(
        next_local_date,
        datetime.min.time(),
        tzinfo=APPLICATION_TIME_ZONE,
    )
    return local_start.astimezone(timezone.utc), local_end.astimezone(timezone.utc)


def count_matching_searches(
    history: list[SearchHistory],
    user_id: str,
    query: str,
    current_time: datetime,
) -> int:
    """Count one user's equivalent searches on the current application day."""
    normalized_query = normalize_search_query(query)
    day_start, day_end = application_day_utc_bounds(current_time)
    return sum(
        1
        for record in history
        if record.user_id == user_id
        and normalize_search_query(record.query) == normalized_query
        and day_start <= require_aware_datetime(record.searched_at).astimezone(timezone.utc)
        < day_end
    )


def pricing_context(daily_search_count: int | None) -> SearchPricing:
    """Choose the one-time multiplier for an anonymous or signed-in search."""
    adjustment_applied = (
        daily_search_count is not None and daily_search_count >= URGENCY_THRESHOLD
    )
    multiplier = URGENCY_MULTIPLIER if adjustment_applied else BASE_MULTIPLIER
    return SearchPricing(
        daily_search_count=daily_search_count,
        multiplier=multiplier,
        adjustment_applied=adjustment_applied,
        time_zone=APPLICATION_TIME_ZONE_NAME,
    )


def calculate_price_quote(
    base_nightly_rate_cents: int,
    nights: int,
    pricing: SearchPricing,
) -> PriceQuote:
    """Calculate effective prices from the immutable stored base rate."""
    if base_nightly_rate_cents < 0:
        raise ValueError("Base nightly rate cannot be negative.")
    if nights <= 0:
        raise ValueError("A stay must contain at least one night.")

    base_nightly_rate = (Decimal(base_nightly_rate_cents) / 100).quantize(ONE_CENT)
    effective_nightly_rate = (base_nightly_rate * pricing.multiplier).quantize(
        ONE_CENT,
        rounding=ROUND_HALF_UP,
    )
    return PriceQuote(
        base_nightly_rate_usd=base_nightly_rate,
        nightly_rate_usd=effective_nightly_rate,
        base_stay_price_usd=(base_nightly_rate * nights).quantize(ONE_CENT),
        stay_price_usd=(effective_nightly_rate * nights).quantize(ONE_CENT),
    )
