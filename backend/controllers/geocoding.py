"""Geoapify-backed postcode lookup controller logic."""

from __future__ import annotations

import math
from typing import Any

import httpx

from backend.config import get_geoapify_api_key
from backend.controllers.errors import (
    GeoapifyConfigurationError,
    GeoapifyRequestError,
    PostcodeNotFoundError,
)
from backend.models import PostcodeLocation

GEOAPIFY_FORWARD_GEOCODING_URL = "https://api.geoapify.com/v1/geocode/search"
REQUEST_TIMEOUT_SECONDS = 5.0


def _valid_coordinate(value: Any, minimum: float, maximum: float) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and minimum <= value <= maximum
    )


def _locality(result: dict[str, Any]) -> str | None:
    for field in ("city", "town", "village", "municipality", "locality"):
        value = result.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def lookup_us_postcode(postcode: str) -> PostcodeLocation:
    """Resolve an exact U.S. postcode or raise a typed lookup/provider error."""
    requested_postcode = postcode.strip()
    api_key = get_geoapify_api_key()
    if api_key is None:
        raise GeoapifyConfigurationError("Geoapify API key is not configured.")

    request_failed = False
    try:
        response = httpx.get(
            GEOAPIFY_FORWARD_GEOCODING_URL,
            params={
                "text": requested_postcode,
                "type": "postcode",
                "filter": "countrycode:us",
                "format": "json",
                "apiKey": api_key,
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError):
        request_failed = True

    if request_failed:
        raise GeoapifyRequestError("Geoapify postcode lookup failed.")
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise GeoapifyRequestError("Geoapify returned an invalid postcode response.")

    for result in payload["results"]:
        if not isinstance(result, dict):
            continue
        latitude = result.get("lat")
        longitude = result.get("lon")
        country_code = result.get("country_code")
        if (
            result.get("postcode") == requested_postcode
            and isinstance(country_code, str)
            and country_code.lower() == "us"
            and _valid_coordinate(latitude, -90.0, 90.0)
            and _valid_coordinate(longitude, -180.0, 180.0)
        ):
            return PostcodeLocation(
                postcode=requested_postcode,
                country_code="us",
                latitude=float(latitude),
                longitude=float(longitude),
                locality=_locality(result),
            )

    raise PostcodeNotFoundError(requested_postcode)
