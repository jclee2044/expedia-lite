"""Geoapify Places contract checks without live provider requests."""

from unittest.mock import Mock

import httpx
import pytest

import backend.controllers.places as places
from backend.controllers.errors import GeoapifyRequestError
from backend.models import PostcodeLocation


def _center() -> PostcodeLocation:
    return PostcodeLocation("00501", "us", 40.8154, -73.0451, "Holtsville")


def _response(features: list[object]) -> httpx.Response:
    return httpx.Response(
        200,
        json={"type": "FeatureCollection", "features": features},
        request=httpx.Request("GET", places.PLACES_URL),
    )


def _feature(place_id: str, name: str | None = "Harbor Hotel") -> dict[str, object]:
    return {
        "type": "Feature",
        "properties": {"place_id": place_id, "name": name, "formatted": "1 Example St"},
        "geometry": {"type": "Point", "coordinates": [-73.04, 40.82]},
    }


def test_nearby_search_uses_resolved_point_and_returns_distinct_places(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    geocode = Mock(return_value=_center())
    get = Mock(return_value=_response([_feature("p1"), _feature("p1"), _feature("p2", None)]))
    monkeypatch.setattr(places, "lookup_us_postcode", geocode)
    monkeypatch.setattr(places, "get_geoapify_api_key", lambda: "synthetic-key")
    monkeypatch.setattr(places.httpx, "get", get)

    search = places.search_nearby_hotels("00501")

    geocode.assert_called_once_with("00501")
    assert search.center == _center()
    assert search.radius_meters == 5000
    assert search.result_limit == 50
    assert [hotel.place_id for hotel in search.hotels] == ["p1", "p2"]
    assert search.hotels[1].name is None
    assert get.call_args.args == (places.PLACES_URL,)
    assert get.call_args.kwargs == {
        "params": {
            "categories": "accommodation.hotel",
            "filter": "circle:-73.0451,40.8154,5000",
            "bias": "proximity:-73.0451,40.8154",
            "limit": 50,
            "apiKey": "synthetic-key",
        },
        "timeout": 5.0,
    }


def test_nearby_search_rejects_an_unusable_provider_response(monkeypatch: pytest.MonkeyPatch) -> None:
    bad_coordinate = _feature("p2")
    bad_coordinate["geometry"] = {"type": "Point", "coordinates": [200, 40.82]}
    monkeypatch.setattr(places, "lookup_us_postcode", lambda postcode: _center())
    monkeypatch.setattr(places, "get_geoapify_api_key", lambda: "synthetic-key")
    monkeypatch.setattr(places.httpx, "get", lambda *args, **kwargs: _response([{}, bad_coordinate]))

    with pytest.raises(GeoapifyRequestError):
        places.search_nearby_hotels("00501")


def test_nearby_search_distinguishes_provider_failure_from_empty_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(places, "lookup_us_postcode", lambda postcode: _center())
    monkeypatch.setattr(places, "get_geoapify_api_key", lambda: "synthetic-key")
    monkeypatch.setattr(places.httpx, "get", lambda *args, **kwargs: _response([]))
    assert places.search_nearby_hotels("00501").hotels == []

    request = httpx.Request("GET", places.PLACES_URL)
    monkeypatch.setattr(
        places.httpx,
        "get",
        Mock(side_effect=httpx.ConnectTimeout("credential-bearing detail", request=request)),
    )
    with pytest.raises(GeoapifyRequestError) as captured:
        places.search_nearby_hotels("00501")
    assert "credential" not in str(captured.value)
