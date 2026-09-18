import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from backend.controllers.accounts import authenticate, create_account
from backend.controllers.database import connect_database, initialize_database
from backend.controllers.errors import (
    AccountValidationError,
    AuthenticationError,
    DuplicateUsernameError,
)
from backend.controllers.sessions import SessionStore

DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"


@pytest.fixture
def connection(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    database_path = tmp_path / "expedia.sqlite3"
    initialize_database(database_path, DATA_DIRECTORY)
    database = connect_database(database_path)
    try:
        yield database
    finally:
        database.close()


def test_create_account_normalizes_fields_and_allocates_id(
    connection: sqlite3.Connection,
) -> None:
    account = create_account(
        connection,
        "  harbor_fan  ",
        "made-up-pass",
        "  harbor@example.test  ",
    )

    assert account.user_id == "U007"
    assert account.display_name == "harbor_fan"
    assert account.username == "harbor_fan"
    assert account.email == "harbor@example.test"
    assert not hasattr(account, "password")
    stored = connection.execute(
        "SELECT password FROM users WHERE user_id = 'U007'"
    ).fetchone()
    assert stored["password"] == "made-up-pass"


def test_duplicate_username_is_case_insensitive_and_does_not_consume_id(
    connection: sqlite3.Connection,
) -> None:
    create_account(connection, "HarborFan", "demo-pass")

    with pytest.raises(DuplicateUsernameError, match="already in use"):
        create_account(connection, "harborfan", "other-pass")

    next_account = create_account(connection, "CapitolFan", "demo-pass")
    assert next_account.user_id == "U008"


def test_authentication_is_case_insensitive_for_username_and_exact_for_password(
    connection: sqlite3.Connection,
) -> None:
    expected = create_account(connection, "HarborFan", "Exact-Pass")

    assert authenticate(connection, "harborfan", "Exact-Pass") == expected
    with pytest.raises(AuthenticationError, match="username or password"):
        authenticate(connection, "HarborFan", "exact-pass")
    with pytest.raises(AuthenticationError, match="username or password"):
        authenticate(connection, "missing", "Exact-Pass")


@pytest.mark.parametrize(
    ("username", "password", "email", "message"),
    [
        ("a", "demo-pass", None, "Username must be"),
        ("bad name", "demo-pass", None, "Username must be"),
        ("valid_name", "abc", None, "Password must be"),
        ("valid_name", "demo-pass", "invalid", "valid email"),
    ],
)
def test_account_validation_rejects_invalid_fields_without_writing(
    connection: sqlite3.Connection,
    username: str,
    password: str,
    email: str | None,
    message: str,
) -> None:
    with pytest.raises(AccountValidationError, match=message):
        create_account(connection, username, password, email)

    assert connection.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 6


def test_session_store_resolves_invalidates_and_expires_tokens() -> None:
    now = [100.0]
    sessions = SessionStore(lifetime_seconds=10, clock=lambda: now[0])
    token = sessions.create("U001")

    assert sessions.resolve(token) == "U001"
    now[0] = 111.0
    assert sessions.resolve(token) is None

    replacement = sessions.create("U002")
    sessions.invalidate(replacement)
    assert sessions.resolve(replacement) is None
