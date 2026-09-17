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
        yield test_client


def test_list_users_returns_seeded_travelers(client: TestClient) -> None:
    response = client.get("/api/users")

    assert response.status_code == 200
    body = response.json()
    assert [user["user_id"] for user in body["users"]] == [
        "U001",
        "U002",
        "U003",
        "U004",
        "U005",
        "U006",
    ]
    assert body["users"][0] == {
        "user_id": "U001",
        "display_name": "Demo Traveler 1",
    }


def test_seeded_and_empty_history_contracts(client: TestClient) -> None:
    seeded_response = client.get("/api/users/U001/bookings")
    empty_response = client.get("/api/users/U006/bookings")

    assert seeded_response.status_code == 200
    seeded = seeded_response.json()
    assert seeded["user"] == {
        "user_id": "U001",
        "display_name": "Demo Traveler 1",
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
        },
        "booking_count": 0,
        "bookings": [],
    }


def test_booking_crud_flow_preserves_cancel_and_delete_semantics(
    client: TestClient,
) -> None:
    create_response = client.post(
        "/api/bookings", json={"user_id": "U006", "trip_id": "T009"}
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
    history_response = client.get("/api/users/U006/bookings")
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
    assert client.get("/api/users/U006/bookings").json()["booking_count"] == 0

    next_response = client.post(
        "/api/bookings", json={"user_id": "U006", "trip_id": "T009"}
    )
    assert next_response.status_code == 201
    assert next_response.json()["booking_id"] == "B008"


@pytest.mark.parametrize(
    ("payload", "expected_detail"),
    [
        ({"user_id": "U999", "trip_id": "T001"}, "User U999 was not found."),
        ({"user_id": "U006", "trip_id": "T999"}, "Trip T999 was not found."),
    ],
)
def test_create_booking_rejects_missing_relations(
    client: TestClient,
    payload: dict[str, str],
    expected_detail: str,
) -> None:
    response = client.post("/api/bookings", json=payload)

    assert response.status_code == 404
    assert response.json() == {"detail": expected_detail}


@pytest.mark.parametrize(
    ("method", "path", "json"),
    [
        ("get", "/api/users/U999/bookings", None),
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
        ("post", "/api/bookings", {"user_id": "invalid", "trip_id": "T001"}),
        ("post", "/api/bookings", {"user_id": "U006"}),
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
            "/api/bookings", json={"user_id": "U006", "trip_id": "T001"}
        )
        assert create_response.status_code == 201

    with TestClient(create_app(database_path, DATA_DIRECTORY)) as second_client:
        booking_response = second_client.get("/api/bookings/B007")
        history_response = second_client.get("/api/users/U006/bookings")

    assert booking_response.status_code == 200
    assert booking_response.json() == create_response.json()
    assert history_response.json()["bookings"] == [create_response.json()]
