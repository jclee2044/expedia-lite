"""Find Geoapify hotel places around an exact U.S. ZIP location."""

from __future__ import annotations

import math
from typing import Any

import httpx

from backend.config import get_geoapify_api_key
from backend.controllers.errors import GeoapifyConfigurationError, GeoapifyRequestError
from backend.controllers.geocoding import REQUEST_TIMEOUT_SECONDS, lookup_us_postcode
from backend.models import ExternalHotel, NearbyHotelSearch

PLACES_URL = "https://api.geoapify.com/v2/places"
RADIUS_METERS = 5_000
RESULT_LIMIT = 50


def _coordinate(value: Any, minimum: float, maximum: float) -> float | None:
    if (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and minimum <= value <= maximum
    ):
        return float(value)
    return None


def _optional_text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _hotel_from_feature(feature: Any) -> ExternalHotel | None:
    if not isinstance(feature, dict):
        return None
    properties = feature.get("properties")
    geometry = feature.get("geometry")
    if not isinstance(properties, dict) or not isinstance(geometry, dict):
        return None
    coordinates = geometry.get("coordinates")
    if geometry.get("type") != "Point" or not isinstance(coordinates, list) or len(coordinates) < 2:
        return None
    longitude = _coordinate(coordinates[0], -180, 180)
    latitude = _coordinate(coordinates[1], -90, 90)
    place_id = _optional_text(properties.get("place_id"))
    if place_id is None or latitude is None or longitude is None:
        return None
    return ExternalHotel(
        place_id=place_id,
        name=_optional_text(properties.get("name")),
        address=_optional_text(properties.get("formatted")),
        latitude=latitude,
        longitude=longitude,
    )


def search_nearby_hotels(postcode: str) -> NearbyHotelSearch:
    """Resolve the ZIP, then return usable hotel places within its 5 km circle."""
    center = lookup_us_postcode(postcode)
    api_key = get_geoapify_api_key()
    if api_key is None:
        raise GeoapifyConfigurationError("Geoapify API key is not configured.")

    try:
        response = httpx.get(
            PLACES_URL,
            params={
                "categories": "accommodation.hotel",
                "filter": f"circle:{center.longitude},{center.latitude},{RADIUS_METERS}",
                "bias": f"proximity:{center.longitude},{center.latitude}",
                "limit": RESULT_LIMIT,
                "apiKey": api_key,
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError):
        raise GeoapifyRequestError("Geoapify hotel search failed.") from None

    if not isinstance(payload, dict) or not isinstance(payload.get("features"), list):
        raise GeoapifyRequestError("Geoapify returned an invalid hotel response.")

    hotels: list[ExternalHotel] = []
    seen: set[str] = set()
    for feature in payload["features"]:
        hotel = _hotel_from_feature(feature)
        if hotel is not None and hotel.place_id not in seen:
            seen.add(hotel.place_id)
            hotels.append(hotel)

    if payload["features"] and not hotels:
        raise GeoapifyRequestError("Geoapify returned no usable hotel places.")

    return NearbyHotelSearch(
        center=center,
        radius_meters=RADIUS_METERS,
        result_limit=RESULT_LIMIT,
        hotels=hotels,
    )
