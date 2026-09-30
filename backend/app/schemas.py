"""JSON response schemas for the Expedia Lite API."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: Literal["ok"]
    geoapify_api_key: Literal[
        "key is configured",
        "key is not configured",
    ]


class PostcodeLocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    postcode: str
    country_code: str
    latitude: float
    longitude: float
    locality: str | None


class ExternalHotelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    place_id: str
    name: str | None
    address: str | None
    latitude: float
    longitude: float


class NearbyHotelSearchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    center: PostcodeLocationResponse
    radius_meters: int
    result_limit: int
    hotels: list[ExternalHotelResponse]


class HotelStayResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    hotel_id: str
    hotel_name: str
    city: str
    state: str
    trip_id: str
    trip_name: str
    check_in: date
    check_out: date
    nights: int
    base_nightly_rate_usd: float
    nightly_rate_usd: float
    base_stay_price_usd: float
    stay_price_usd: float


class SearchPricingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    daily_search_count: int | None
    multiplier: float
    adjustment_applied: bool
    time_zone: str


class HotelSearchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    query: str
    hotel_count: int
    pricing: SearchPricingResponse
    results: list[HotelStayResponse]


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    display_name: str
    username: str
    email: str | None


class AccountCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=4, max_length=72)
    email: str | None = Field(default=None, max_length=254)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=1, max_length=72)


class BookingCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trip_id: str = Field(pattern=r"^T\d+$")
    search_query: str | None = Field(default=None, min_length=1, max_length=200)


class BookingStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["confirmed", "cancelled"]


class BookingDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    nightly_rate_usd: float
    stay_price_usd: float
    booked_on: date
    status: Literal["confirmed", "cancelled"]


class BookingHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user: AccountResponse
    booking_count: int
    bookings: list[BookingDetailResponse]
