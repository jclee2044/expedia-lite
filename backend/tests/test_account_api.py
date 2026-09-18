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


def test_account_creation_auto_logs_in_and_never_returns_password(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/accounts",
        json={
            "username": "harbor_fan",
            "password": "made-up-pass",
            "email": "harbor@example.test",
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "user_id": "U007",
        "display_name": "harbor_fan",
        "username": "harbor_fan",
        "email": "harbor@example.test",
    }
    assert "password" not in response.text
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "SameSite=lax" in response.headers["set-cookie"]
    assert client.get("/api/auth/session").json() == response.json()
    assert client.get("/api/account/bookings").json()["bookings"] == []


def test_duplicate_username_is_case_insensitive(client: TestClient) -> None:
    first = client.post(
        "/api/accounts",
        json={"username": "HarborFan", "password": "made-up-pass"},
    )
    duplicate = client.post(
        "/api/accounts",
        json={"username": "harborfan", "password": "another-pass"},
    )

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert duplicate.json() == {"detail": "That username is already in use."}


@pytest.mark.parametrize(
    "payload",
    [
        {"username": "bad name", "password": "made-up-pass"},
        {"username": "valid_name", "password": "made-up-pass", "email": "bad"},
        {"username": "valid_name", "password": "abc"},
        {"username": "valid_name", "password": "made-up-pass", "extra": True},
    ],
)
def test_account_creation_rejects_invalid_input(
    client: TestClient, payload: dict[str, object]
) -> None:
    response = client.post("/api/accounts", json=payload)

    assert response.status_code in {400, 422}


def test_login_logout_and_generic_login_error(client: TestClient) -> None:
    wrong_password = client.post(
        "/api/auth/login",
        json={"username": "demo_u001", "password": "wrong-pass"},
    )
    missing_user = client.post(
        "/api/auth/login",
        json={"username": "missing", "password": "wrong-pass"},
    )

    assert wrong_password.status_code == 401
    assert missing_user.status_code == 401
    assert wrong_password.json() == missing_user.json() == {
        "detail": "The username or password is incorrect."
    }

    login = client.post(
        "/api/auth/login",
        json={"username": "DEMO_U001", "password": "demo-pass-u001"},
    )
    assert login.status_code == 200
    assert login.json()["user_id"] == "U001"
    assert "password" not in login.text

    logout = client.post("/api/auth/logout")
    assert logout.status_code == 204
    assert client.get("/api/auth/session").status_code == 401


@pytest.mark.parametrize(
    ("method", "path", "json"),
    [
        ("get", "/api/auth/session", None),
        ("get", "/api/account/bookings", None),
        ("post", "/api/bookings", {"trip_id": "T001"}),
        ("get", "/api/bookings/B001", None),
        ("patch", "/api/bookings/B001", {"status": "cancelled"}),
        ("delete", "/api/bookings/B001", None),
    ],
)
def test_account_routes_require_login(
    client: TestClient,
    method: str,
    path: str,
    json: dict[str, str] | None,
) -> None:
    response = client.request(method, path, json=json)

    assert response.status_code == 401
    assert response.json() == {"detail": "Log in to continue."}


def test_booking_routes_hide_other_accounts_records(client: TestClient) -> None:
    assert client.post(
        "/api/auth/login",
        json={"username": "demo_u001", "password": "demo-pass-u001"},
    ).status_code == 200

    assert client.get("/api/bookings/B001").status_code == 200
    assert client.get("/api/bookings/B003").status_code == 404
    assert client.patch(
        "/api/bookings/B003", json={"status": "cancelled"}
    ).status_code == 404
    assert client.delete("/api/bookings/B003").status_code == 404


def test_account_persists_but_session_does_not_survive_app_restart(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "expedia.sqlite3"
    first_app = create_app(database_path, DATA_DIRECTORY)
    with TestClient(first_app) as first_client:
        assert first_client.post(
            "/api/accounts",
            json={"username": "restart_user", "password": "made-up-pass"},
        ).status_code == 201

    second_app = create_app(database_path, DATA_DIRECTORY)
    with TestClient(second_app) as second_client:
        assert second_client.get("/api/auth/session").status_code == 401
        login = second_client.post(
            "/api/auth/login",
            json={"username": "restart_user", "password": "made-up-pass"},
        )
        assert login.status_code == 200
        assert login.json()["user_id"] == "U007"
