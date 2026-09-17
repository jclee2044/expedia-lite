import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app

DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    application = create_app(tmp_path / "expedia.sqlite3", DATA_DIRECTORY)
    with TestClient(application) as test_client:
        yield test_client


def test_search_endpoint_returns_documented_contract(client: TestClient) -> None:
    response = client.get("/api/hotels/search", params={"name": "Harbor"})

    assert response.status_code == 200
    assert response.json() == {
        "query": "Harbor",
        "hotel_count": 1,
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
                "nightly_rate_usd": 150.0,
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
                "nightly_rate_usd": 150.0,
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
        "results": [],
    }


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
