"""Framework-free entity and read models for Expedia Lite."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
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
    """A persisted synthetic traveler."""

    user_id: str
    display_name: str


@dataclass(frozen=True)
class Booking:
    """A persisted booking that references one user and one trip."""

    booking_id: str
    user_id: str
    trip_id: str
    booked_on: date
    status: BookingStatus


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
    nightly_rate_usd: Decimal
    stay_price_usd: Decimal


@dataclass(frozen=True)
class HotelSearch:
    """A normalized hotel search and its matching stays."""

    query: str
    hotel_count: int
    results: list[HotelStay]


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

    user: User
    booking_count: int
    bookings: list[BookingDetail]
