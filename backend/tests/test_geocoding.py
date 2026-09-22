"""Mocked checks for the Geoapify postcode controller."""

from unittest.mock import Mock

import httpx
import pytest

import backend.controllers.geocoding as geocoding
from backend.controllers.errors import GeoapifyRequestError, PostcodeNotFoundError
from backend.models import PostcodeLocation

SYNTHETIC_API_KEY = "synthetic-test-key"


def _response(results: list[dict[str, object]]) -> httpx.Response:
    request = httpx.Request("GET", geocoding.GEOAPIFY_FORWARD_GEOCODING_URL)
    return httpx.Response(200, json={"results": results}, request=request)


def test_lookup_us_postcode_returns_matching_location(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get = Mock(
        return_value=_response(
            [
                {
                    "postcode": "16802",
                    "country_code": "us",
                    "lat": 40.7982,
                    "lon": -77.8599,
                    "city": "University Park",
                }
            ]
        )
    )
    monkeypatch.setattr(geocoding, "get_geoapify_api_key", lambda: SYNTHETIC_API_KEY)
    monkeypatch.setattr(geocoding.httpx, "get", get)

    location = geocoding.lookup_us_postcode("16802")

    assert location == PostcodeLocation(
        postcode="16802",
        country_code="us",
        latitude=40.7982,
        longitude=-77.8599,
        locality="University Park",
    )
    assert get.call_args.kwargs == {
        "params": {
            "text": "16802",
            "type": "postcode",
            "filter": "countrycode:us",
            "format": "json",
            "apiKey": SYNTHETIC_API_KEY,
        },
        "timeout": 5.0,
    }
    assert get.call_args.args == (geocoding.GEOAPIFY_FORWARD_GEOCODING_URL,)


@pytest.mark.parametrize(
    "result",
    [
        {"postcode": "16801", "country_code": "us", "lat": 40.7, "lon": -77.8},
        {"postcode": "16802", "country_code": "ca", "lat": 40.7, "lon": -77.8},
        {"postcode": "16802", "country_code": "us", "lat": 100.0, "lon": -77.8},
    ],
)
def test_lookup_us_postcode_rejects_mismatched_or_invalid_location(
    monkeypatch: pytest.MonkeyPatch,
    result: dict[str, object],
) -> None:
    monkeypatch.setattr(geocoding, "get_geoapify_api_key", lambda: SYNTHETIC_API_KEY)
    monkeypatch.setattr(geocoding.httpx, "get", lambda *args, **kwargs: _response([result]))

    with pytest.raises(PostcodeNotFoundError, match="16802"):
        geocoding.lookup_us_postcode("16802")


def test_lookup_us_postcode_sanitizes_provider_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = httpx.Request("GET", geocoding.GEOAPIFY_FORWARD_GEOCODING_URL)
    monkeypatch.setattr(geocoding, "get_geoapify_api_key", lambda: SYNTHETIC_API_KEY)
    monkeypatch.setattr(
        geocoding.httpx,
        "get",
        Mock(side_effect=httpx.ConnectTimeout("credential-bearing detail", request=request)),
    )

    with pytest.raises(GeoapifyRequestError) as captured:
        geocoding.lookup_us_postcode("16802")

    assert str(captured.value) == "Geoapify postcode lookup failed."
    assert SYNTHETIC_API_KEY not in str(captured.value)
    assert captured.value.__context__ is None
