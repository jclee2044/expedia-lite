import shutil
import sqlite3
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

import backend.app.main as app_main
import backend.app.routes as app_routes
from backend.app.main import create_app
from backend.controllers.errors import (
    GeoapifyConfigurationError,
    GeoapifyRequestError,
    PostcodeNotFoundError,
)
from backend.models import PostcodeLocation

DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    application = create_app(tmp_path / "expedia.sqlite3", DATA_DIRECTORY)
    with TestClient(application) as test_client:
        yield test_client


@pytest.mark.parametrize(
    ("configured", "expected_status"),
    [
        (True, "key is configured"),
        (False, "key is not configured"),
    ],
)
def test_health_reports_only_geoapify_configuration_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    configured: bool,
    expected_status: str,
) -> None:
    monkeypatch.setattr(
        app_main,
        "geoapify_key_is_configured",
        lambda: configured,
    )
    application = create_app(tmp_path / "expedia.sqlite3", DATA_DIRECTORY)

    with TestClient(application) as test_client:
        response = test_client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "geoapify_api_key": expected_status,
    }


def test_demo_zip_location_returns_mocked_controller_result(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    controller = Mock(
        return_value=PostcodeLocation(
            postcode="16802",
            country_code="us",
            latitude=40.7982,
            longitude=-77.8599,
            locality="University Park",
        )
    )
    monkeypatch.setattr(app_routes, "lookup_us_postcode", controller)

    response = client.get("/api/demo/zip-location")

    assert response.status_code == 200
    assert response.json() == {
        "postcode": "16802",
        "country_code": "us",
        "latitude": 40.7982,
        "longitude": -77.8599,
        "locality": "University Park",
    }
    controller.assert_called_once_with("16802")


@pytest.mark.parametrize(
    ("controller_error", "status_code", "detail"),
    [
        (
            GeoapifyConfigurationError("credential-bearing detail"),
            503,
            "ZIP location service is not configured.",
        ),
        (
            PostcodeNotFoundError("16802"),
            404,
            "ZIP code 16802 could not be resolved.",
        ),
        (
            GeoapifyRequestError("credential-bearing detail"),
            502,
            "ZIP location provider is unavailable.",
        ),
    ],
)
def test_demo_zip_location_maps_controller_errors_without_details(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    controller_error: Exception,
    status_code: int,
    detail: str,
) -> None:
    controller = Mock(side_effect=controller_error)
    monkeypatch.setattr(app_routes, "lookup_us_postcode", controller)

    response = client.get("/api/demo/zip-location")

    assert response.status_code == status_code
    assert response.json() == {"detail": detail}
    assert "credential" not in response.text
    controller.assert_called_once_with("16802")


def test_search_endpoint_returns_documented_contract(client: TestClient) -> None:
    response = client.get("/api/hotels/search", params={"name": "Harbor"})

    assert response.status_code == 200
    assert response.json() == {
        "query": "Harbor",
        "hotel_count": 1,
        "pricing": {
            "daily_search_count": None,
            "multiplier": 1.0,
            "adjustment_applied": False,
            "time_zone": "America/New_York",
        },
        "results": [
            {
                "hotel_id": "H001",
                "hotel_name": "Harbor Lantern Hotel",
                "city": "Boston",
                "state": "MA",
                "trip_id": "T001",
                "trip_name": "Boston Harbor Weekend",
                "check_in": "2026-09-18",
                "check_out": "2026-09-20",
                "nights": 2,
                "base_nightly_rate_usd": 150.0,
                "nightly_rate_usd": 150.0,
                "base_stay_price_usd": 300.0,
                "stay_price_usd": 300.0,
            },
            {
                "hotel_id": "H001",
                "hotel_name": "Harbor Lantern Hotel",
                "city": "Boston",
                "state": "MA",
                "trip_id": "T009",
                "trip_name": "Boston Autumn Weekend",
                "check_in": "2026-10-02",
                "check_out": "2026-10-04",
                "nights": 2,
                "base_nightly_rate_usd": 150.0,
                "nightly_rate_usd": 150.0,
                "base_stay_price_usd": 300.0,
                "stay_price_usd": 300.0,
            },
        ],
    }


def test_search_endpoint_returns_empty_contract_for_no_match(
    client: TestClient,
) -> None:
    response = client.get("/api/hotels/search", params={"name": "Unknown"})

    assert response.status_code == 200
    assert response.json() == {
        "query": "Unknown",
        "hotel_count": 0,
        "pricing": {
            "daily_search_count": None,
            "multiplier": 1.0,
            "adjustment_applied": False,
            "time_zone": "America/New_York",
        },
        "results": [],
    }


def test_signed_in_searches_receive_personalized_prices(client: TestClient) -> None:
    login_response = client.post(
        "/api/auth/login",
        json={"username": "demo_u001", "password": "demo-pass-u001"},
    )
    assert login_response.status_code == 200

    responses = [
        client.get("/api/hotels/search", params={"name": query})
        for query in ("Valley Trail", " valley trail ", "VALLEY TRAIL", "Valley Trail")
    ]

    assert [response.status_code for response in responses] == [200, 200, 200, 200]
    assert [response.json()["pricing"]["daily_search_count"] for response in responses] == [
        1, 2, 3, 4
    ]
    assert [response.json()["results"][0]["nightly_rate_usd"] for response in responses] == [
        100.0, 100.0, 100.0, 120.0
    ]
    fourth_stay = responses[-1].json()["results"][0]
    assert fourth_stay["base_nightly_rate_usd"] == 100.0
    assert fourth_stay["nightly_rate_usd"] == 120.0


def test_search_history_survives_restart_and_base_price_does_not_change(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "expedia.sqlite3"
    credentials = {"username": "demo_u001", "password": "demo-pass-u001"}
    with TestClient(create_app(database_path, DATA_DIRECTORY)) as first_client:
        assert first_client.post("/api/auth/login", json=credentials).status_code == 200
        for _ in range(3):
            response = first_client.get(
                "/api/hotels/search", params={"name": "Valley Trail"}
            )
            assert response.status_code == 200

    with TestClient(create_app(database_path, DATA_DIRECTORY)) as second_client:
        assert second_client.post("/api/auth/login", json=credentials).status_code == 200
        response = second_client.get(
            "/api/hotels/search", params={"name": "Valley Trail"}
        )

    assert response.json()["pricing"]["daily_search_count"] == 4
    assert response.json()["results"][0]["nightly_rate_usd"] == 120.0
    connection = sqlite3.connect(database_path)
    try:
        stored_base = connection.execute(
            "SELECT nightly_rate_cents FROM hotels WHERE hotel_id = 'H008'"
        ).fetchone()[0]
        history_count = connection.execute(
            "SELECT COUNT(*) FROM search_history WHERE user_id = 'U001'"
        ).fetchone()[0]
    finally:
        connection.close()
    assert stored_base == 10_000
    assert history_count == 4


def test_search_endpoint_rejects_blank_name(client: TestClient) -> None:
    response = client.get("/api/hotels/search", params={"name": "   "})

    assert response.status_code == 400
    assert response.json() == {"detail": "Enter a hotel name."}


def test_search_endpoint_requires_name(client: TestClient) -> None:
    response = client.get("/api/hotels/search")

    assert response.status_code == 422


def test_restart_uses_sqlite_without_reading_seed_files(tmp_path: Path) -> None:
    seed_directory = tmp_path / "seed"
    seed_directory.mkdir()
    for filename in ("hotels.csv", "trips.csv", "users.csv", "bookings.csv"):
        shutil.copyfile(DATA_DIRECTORY / filename, seed_directory / filename)

    database_path = tmp_path / "expedia.sqlite3"
    with TestClient(create_app(database_path, seed_directory)) as first_client:
        first_response = first_client.get(
            "/api/hotels/search", params={"name": "Harbor"}
        )
    assert first_response.status_code == 200

    for seed_file in seed_directory.iterdir():
        seed_file.unlink()

    with TestClient(create_app(database_path, seed_directory)) as second_client:
        second_response = second_client.get(
            "/api/hotels/search", params={"name": "Harbor"}
        )

    assert second_response.status_code == 200
    assert second_response.json() == first_response.json()
