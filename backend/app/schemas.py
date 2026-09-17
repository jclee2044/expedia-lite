"""JSON response schemas for the Expedia Lite API."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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
    nightly_rate_usd: float
    stay_price_usd: float


class HotelSearchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    query: str
    hotel_count: int
    results: list[HotelStayResponse]


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    display_name: str


class UserListResponse(BaseModel):
    users: list[UserResponse]


class BookingCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(pattern=r"^U\d+$")
    trip_id: str = Field(pattern=r"^T\d+$")


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

    user: UserResponse
    booking_count: int
    bookings: list[BookingDetailResponse]
