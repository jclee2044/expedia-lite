"""Framework-free entity and read models for Expedia Lite."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

BookingStatus = Literal["confirmed", "cancelled"]


@dataclass(frozen=True)
class Hotel:
    """A persisted hotel entity."""

    hotel_id: str
    hotel_name: str
    city: str
    state: str
    nightly_rate_cents: int


@dataclass(frozen=True)
class Trip:
    """A persisted trip that references one hotel."""

    trip_id: str
    hotel_id: str
    trip_name: str
    check_in: date
    check_out: date


@dataclass(frozen=True)
class User:
    """A persisted classroom account, including its demo credential."""

    user_id: str
    display_name: str
    username: str
    password: str
    email: str | None


@dataclass(frozen=True)
class AccountProfile:
    """A safe account projection that never exposes the stored password."""

    user_id: str
    display_name: str
    username: str
    email: str | None


@dataclass(frozen=True)
class Booking:
    """A persisted booking that references one user and one trip."""

    booking_id: str
    user_id: str
    trip_id: str
    booked_on: date
    status: BookingStatus


@dataclass(frozen=True)
class SearchHistory:
    """One persisted normalized hotel-name search by an account."""

    search_id: int
    user_id: str
    query: str
    searched_at: datetime


@dataclass(frozen=True)
class PriceQuote:
    """Base and effective prices calculated for one offered stay."""

    base_nightly_rate_usd: Decimal
    nightly_rate_usd: Decimal
    base_stay_price_usd: Decimal
    stay_price_usd: Decimal


@dataclass(frozen=True)
class SearchPricing:
    """Pricing context shared by every result in one search response."""

    daily_search_count: int | None
    multiplier: Decimal
    adjustment_applied: bool
    time_zone: str


@dataclass(frozen=True)
class HotelStay:
    """A hotel and trip projection displayed by search."""

    hotel_id: str
    hotel_name: str
    city: str
    state: str
    trip_id: str
    trip_name: str
    check_in: date
    check_out: date
    nights: int
    base_nightly_rate_usd: Decimal
    nightly_rate_usd: Decimal
    base_stay_price_usd: Decimal
    stay_price_usd: Decimal


@dataclass(frozen=True)
class HotelSearch:
    """A normalized hotel search and its matching stays."""

    query: str
    hotel_count: int
    pricing: SearchPricing
    results: list[HotelStay]


@dataclass(frozen=True)
class PostcodeLocation:
    """A resolved postcode location without hotel or price data."""

    postcode: str
    country_code: str
    latitude: float
    longitude: float
    locality: str | None


@dataclass(frozen=True)
class ExternalHotel:
    """A Geoapify place; it has no booking or nightly-rate claim."""

    place_id: str
    name: str | None
    address: str | None
    latitude: float
    longitude: float


@dataclass(frozen=True)
class NearbyHotelSearch:
    """Hotels returned within a fixed radius of a resolved ZIP point."""

    center: PostcodeLocation
    radius_meters: int
    result_limit: int
    hotels: list[ExternalHotel]


@dataclass(frozen=True)
class DemoHotelNight:
    """Fictional classroom rate and room count for one saved hotel night."""

    stay_date: str
    nightly_rate_cents: int
    rooms_available: int


@dataclass(frozen=True)
class SavedHotel:
    """A provider hotel persisted locally with its demo nightly inventory."""

    place_id: str
    name: str | None
    address: str | None
    latitude: float
    longitude: float
    nights: list[DemoHotelNight]


@dataclass(frozen=True)
class SavedHotelSearch:
    """ZIP-specific saved hotels plus provider IDs saved anywhere locally."""

    center: PostcodeLocation | None
    hotels: list[SavedHotel]
    saved_place_ids: list[str]


@dataclass(frozen=True)
class BookingDetail:
    """A booking joined to its user, trip, and hotel for display."""

    booking_id: str
    user_id: str
    display_name: str
    trip_id: str
    trip_name: str
    hotel_id: str
    hotel_name: str
    city: str
    state: str
    check_in: date
    check_out: date
    nights: int
    nightly_rate_usd: Decimal
    stay_price_usd: Decimal
    booked_on: date
    status: BookingStatus


@dataclass(frozen=True)
class BookingHistory:
    """One user and their joined booking records."""

    user: AccountProfile
    booking_count: int
    bookings: list[BookingDetail]
