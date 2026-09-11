"""JSON response schemas for the Expedia Lite API."""

from datetime import date

from pydantic import BaseModel, ConfigDict


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
