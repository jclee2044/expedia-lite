"""Framework-free account creation and authentication logic."""

from __future__ import annotations

import re
import sqlite3

from backend.controllers.database import (
    allocate_user_id,
    fetch_user,
    fetch_user_by_username,
    insert_user,
)
from backend.controllers.errors import (
    AccountValidationError,
    AuthenticationError,
    DuplicateUsernameError,
    RecordNotFoundError,
)
from backend.controllers.users import account_profile_from_row
from backend.models import AccountProfile

USERNAME_PATTERN = re.compile(r"[A-Za-z0-9_.-]{3,32}")
LOGIN_ERROR = "The username or password is incorrect."


def _validated_username(username: str) -> str:
    cleaned = username.strip()
    if USERNAME_PATTERN.fullmatch(cleaned) is None:
        raise AccountValidationError(
            "Username must be 3–32 characters using letters, numbers, dots, "
            "hyphens, or underscores."
        )
    return cleaned


def _validated_password(password: str) -> str:
    if not 4 <= len(password) <= 72:
        raise AccountValidationError("Password must be 4–72 characters.")
    return password


def _validated_email(email: str | None) -> str | None:
    cleaned = email.strip() if email is not None else ""
    if not cleaned:
        return None
    local, separator, domain = cleaned.partition("@")
    if not separator or not local or "." not in domain:
        raise AccountValidationError("Enter a valid email address or leave it blank.")
    return cleaned


def get_account(connection: sqlite3.Connection, user_id: str) -> AccountProfile:
    """Return a password-free account projection by ID."""
    row = fetch_user(connection, user_id)
    if row is None:
        raise RecordNotFoundError("user", user_id)
    return account_profile_from_row(row)


def create_account(
    connection: sqlite3.Connection,
    username: str,
    password: str,
    email: str | None = None,
) -> AccountProfile:
    """Validate and persist a unique classroom account atomically."""
    clean_username = _validated_username(username)
    clean_password = _validated_password(password)
    clean_email = _validated_email(email)

    try:
        connection.execute("BEGIN IMMEDIATE")
        if fetch_user_by_username(connection, clean_username) is not None:
            raise DuplicateUsernameError("That username is already in use.")
        user_id = allocate_user_id(connection)
        insert_user(
            connection,
            user_id,
            clean_username,
            clean_username,
            clean_password,
            clean_email,
        )
        connection.commit()
    except sqlite3.IntegrityError as error:
        connection.rollback()
        if fetch_user_by_username(connection, clean_username) is not None:
            raise DuplicateUsernameError("That username is already in use.") from error
        raise
    except Exception:
        connection.rollback()
        raise
    return get_account(connection, user_id)


def authenticate(
    connection: sqlite3.Connection, username: str, password: str
) -> AccountProfile:
    """Authenticate exact demo credentials without exposing which field failed."""
    row = fetch_user_by_username(connection, username.strip())
    if row is None or row["password"] != password:
        raise AuthenticationError(LOGIN_ERROR)
    return account_profile_from_row(row)
