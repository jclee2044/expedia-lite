from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_search_endpoint_returns_documented_contract() -> None:
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


def test_search_endpoint_returns_empty_contract_for_no_match() -> None:
    response = client.get("/api/hotels/search", params={"name": "Unknown"})

    assert response.status_code == 200
    assert response.json() == {
        "query": "Unknown",
        "hotel_count": 0,
        "results": [],
    }


def test_search_endpoint_rejects_blank_name() -> None:
    response = client.get("/api/hotels/search", params={"name": "   "})

    assert response.status_code == 400
    assert response.json() == {"detail": "Enter a hotel name."}


def test_search_endpoint_requires_name() -> None:
    response = client.get("/api/hotels/search")

    assert response.status_code == 422
