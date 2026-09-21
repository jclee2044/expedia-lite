from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app

DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    application = create_app(tmp_path / "expedia.sqlite3", DATA_DIRECTORY)
    with TestClient(application) as test_client:
        response = test_client.post(
            "/api/auth/login",
            json={"username": "demo_u006", "password": "demo-pass-u006"},
        )
        assert response.status_code == 200
        yield test_client


def test_seeded_and_empty_history_contracts(client: TestClient) -> None:
    empty_response = client.get("/api/account/bookings")
    client.post("/api/auth/logout")
    assert client.post(
        "/api/auth/login",
        json={"username": "demo_u001", "password": "demo-pass-u001"},
    ).status_code == 200
    seeded_response = client.get("/api/account/bookings")

    assert seeded_response.status_code == 200
    seeded = seeded_response.json()
    assert seeded["user"] == {
        "user_id": "U001",
        "display_name": "Demo Traveler 1",
        "username": "demo_u001",
        "email": "demo_u001@example.test",
    }
    assert seeded["booking_count"] == 2
    assert [booking["booking_id"] for booking in seeded["bookings"]] == [
        "B002",
        "B001",
    ]
    assert seeded["bookings"][1] == {
        "booking_id": "B001",
        "user_id": "U001",
        "display_name": "Demo Traveler 1",
        "trip_id": "T001",
        "trip_name": "Boston Harbor Weekend",
        "hotel_id": "H001",
        "hotel_name": "Harbor Lantern Hotel",
        "city": "Boston",
        "state": "MA",
        "check_in": "2026-09-18",
        "check_out": "2026-09-20",
        "nights": 2,
        "nightly_rate_usd": 150.0,
        "stay_price_usd": 300.0,
        "booked_on": "2026-09-01",
        "status": "confirmed",
    }

    assert empty_response.status_code == 200
    assert empty_response.json() == {
        "user": {
            "user_id": "U006",
            "display_name": "Demo Traveler 6",
            "username": "demo_u006",
            "email": None,
        },
        "booking_count": 0,
        "bookings": [],
    }


def test_booking_crud_flow_preserves_cancel_and_delete_semantics(
    client: TestClient,
) -> None:
    create_response = client.post(
        "/api/bookings", json={"trip_id": "T009"}
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created == {
        "booking_id": "B007",
        "user_id": "U006",
        "display_name": "Demo Traveler 6",
        "trip_id": "T009",
        "trip_name": "Boston Autumn Weekend",
        "hotel_id": "H001",
        "hotel_name": "Harbor Lantern Hotel",
        "city": "Boston",
        "state": "MA",
        "check_in": "2026-10-02",
        "check_out": "2026-10-04",
        "nights": 2,
        "nightly_rate_usd": 150.0,
        "stay_price_usd": 300.0,
        "booked_on": date.today().isoformat(),
        "status": "confirmed",
    }

    get_response = client.get("/api/bookings/B007")
    history_response = client.get("/api/account/bookings")
    assert get_response.json() == created
    assert history_response.json()["bookings"] == [created]

    cancel_response = client.patch(
        "/api/bookings/B007", json={"status": "cancelled"}
    )
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "cancelled"
    assert client.get("/api/bookings/B007").status_code == 200

    delete_response = client.delete("/api/bookings/B007")
    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert client.get("/api/bookings/B007").status_code == 404
    assert client.get("/api/account/bookings").json()["booking_count"] == 0

    next_response = client.post(
        "/api/bookings", json={"trip_id": "T009"}
    )
    assert next_response.status_code == 201
    assert next_response.json()["booking_id"] == "B008"


def test_booking_preserves_the_personalized_search_price(client: TestClient) -> None:
    client.post("/api/auth/logout")
    assert client.post(
        "/api/auth/login",
        json={"username": "demo_u001", "password": "demo-pass-u001"},
    ).status_code == 200
    for _ in range(4):
        response = client.get(
            "/api/hotels/search", params={"name": "Valley Trail"}
        )
        assert response.status_code == 200

    displayed_stay = response.json()["results"][0]
    created = client.post(
        "/api/bookings",
        json={"trip_id": "T008", "search_query": "Valley Trail"},
    )

    assert displayed_stay["nightly_rate_usd"] == 120.0
    assert displayed_stay["stay_price_usd"] == 240.0
    assert created.status_code == 201
    assert created.json()["nightly_rate_usd"] == 120.0
    assert created.json()["stay_price_usd"] == 240.0
    assert client.get("/api/account/bookings").json()["bookings"][0] == created.json()


def test_booking_rejects_unverified_or_mismatched_search_context(
    client: TestClient,
) -> None:
    unverified = client.post(
        "/api/bookings",
        json={"trip_id": "T001", "search_query": "Harbor"},
    )
    assert unverified.status_code == 400
    assert unverified.json() == {"detail": "Search again before booking this stay."}

    assert client.get(
        "/api/hotels/search", params={"name": "Valley Trail"}
    ).status_code == 200
    mismatched = client.post(
        "/api/bookings",
        json={"trip_id": "T001", "search_query": "Valley Trail"},
    )
    assert mismatched.status_code == 400
    assert mismatched.json() == {
        "detail": "The selected stay does not match the current hotel search."
    }
    assert client.get("/api/account/bookings").json()["booking_count"] == 0


def test_create_booking_rejects_missing_relations(
    client: TestClient,
) -> None:
    response = client.post("/api/bookings", json={"trip_id": "T999"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Trip T999 was not found."}


@pytest.mark.parametrize(
    ("method", "path", "json"),
    [
        ("get", "/api/bookings/B999", None),
        ("patch", "/api/bookings/B999", {"status": "cancelled"}),
        ("delete", "/api/bookings/B999", None),
    ],
)
def test_booking_routes_return_not_found(
    client: TestClient,
    method: str,
    path: str,
    json: dict[str, str] | None,
) -> None:
    response = client.request(method, path, json=json)

    assert response.status_code == 404


@pytest.mark.parametrize(
    ("method", "path", "json"),
    [
        ("post", "/api/bookings", {}),
        ("post", "/api/bookings", {"user_id": "U006", "trip_id": "T001"}),
        ("post", "/api/bookings", {"trip_id": "T001", "search_query": ""}),
        ("patch", "/api/bookings/B001", {"status": "pending"}),
        (
            "patch",
            "/api/bookings/B001",
            {"status": "cancelled", "trip_id": "T002"},
        ),
    ],
)
def test_booking_routes_reject_invalid_request_bodies(
    client: TestClient,
    method: str,
    path: str,
    json: dict[str, str],
) -> None:
    response = client.request(method, path, json=json)

    assert response.status_code == 422


def test_created_booking_survives_application_restart(tmp_path: Path) -> None:
    database_path = tmp_path / "expedia.sqlite3"
    with TestClient(create_app(database_path, DATA_DIRECTORY)) as first_client:
        create_response = first_client.post(
            "/api/auth/login",
            json={"username": "demo_u006", "password": "demo-pass-u006"},
        )
        assert create_response.status_code == 200
        create_response = first_client.post(
            "/api/bookings", json={"trip_id": "T001"}
        )
        assert create_response.status_code == 201

    with TestClient(create_app(database_path, DATA_DIRECTORY)) as second_client:
        assert second_client.post(
            "/api/auth/login",
            json={"username": "demo_u006", "password": "demo-pass-u006"},
        ).status_code == 200
        booking_response = second_client.get("/api/bookings/B007")
        history_response = second_client.get("/api/account/bookings")

    assert booking_response.status_code == 200
    assert booking_response.json() == create_response.json()
    assert history_response.json()["bookings"] == [create_response.json()]
