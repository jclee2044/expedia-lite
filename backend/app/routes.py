"""FastAPI routes that adapt HTTP requests to application controllers."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from backend.app.schemas import (
    AccountCreateRequest,
    AccountResponse,
    BookingCreateRequest,
    BookingDetailResponse,
    BookingHistoryResponse,
    BookingStatusUpdateRequest,
    HotelSearchResponse,
    LoginRequest,
)
from backend.controllers.accounts import authenticate, create_account, get_account
from backend.controllers.bookings import (
    create_booking,
    delete_booking,
    get_booking,
    update_booking_status,
)
from backend.controllers.database import connect_database
from backend.controllers.errors import (
    AccountValidationError,
    AuthenticationError,
    BookingValidationError,
    DuplicateUsernameError,
    RecordNotFoundError,
    SearchValidationError,
)
from backend.controllers.search import search_hotel_stays
from backend.controllers.users import list_user_bookings

router = APIRouter()
SESSION_COOKIE = "expedia_session"
SESSION_MAX_AGE = 8 * 60 * 60


def get_database(request: Request) -> Iterator[sqlite3.Connection]:
    """Provide one configured SQLite connection for an HTTP request."""
    connection = connect_database(request.app.state.database_path)
    try:
        yield connection
    finally:
        connection.close()


DatabaseConnection = Annotated[sqlite3.Connection, Depends(get_database)]


def require_authenticated_user(request: Request) -> str:
    """Resolve the current opaque session cookie or return HTTP 401."""
    token = request.cookies.get(SESSION_COOKIE)
    user_id = request.app.state.sessions.resolve(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Log in to continue.")
    return user_id


AuthenticatedUserId = Annotated[str, Depends(require_authenticated_user)]


def optional_authenticated_user(request: Request) -> str | None:
    """Resolve a valid session when present while allowing guest searches."""
    token = request.cookies.get(SESSION_COOKIE)
    return request.app.state.sessions.resolve(token)


OptionalAuthenticatedUserId = Annotated[
    str | None, Depends(optional_authenticated_user)
]


def _not_found(error: RecordNotFoundError) -> HTTPException:
    return HTTPException(status_code=404, detail=str(error))


def _database_unavailable() -> HTTPException:
    return HTTPException(
        status_code=500,
        detail="The booking data could not be loaded.",
    )


@router.get("/api/hotels/search", response_model=HotelSearchResponse)
def search_hotels(
    connection: DatabaseConnection,
    user_id: OptionalAuthenticatedUserId,
    name: str = Query(description="Case-insensitive partial hotel name"),
) -> HotelSearchResponse:
    """Search hotel names and return their joined available stays."""
    try:
        search = search_hotel_stays(name, connection, user_id=user_id)
    except sqlite3.DatabaseError as error:
        raise HTTPException(
            status_code=500,
            detail="The hotel data could not be loaded.",
        ) from error
    except SearchValidationError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return HotelSearchResponse.model_validate(search)


@router.get(
    "/api/account/bookings",
    response_model=BookingHistoryResponse,
)
def get_account_booking_history(
    user_id: AuthenticatedUserId,
    connection: DatabaseConnection,
) -> BookingHistoryResponse:
    """Retrieve the authenticated account's joined booking history."""
    try:
        history = list_user_bookings(connection, user_id)
    except RecordNotFoundError as error:
        raise _not_found(error) from error
    except sqlite3.DatabaseError as error:
        raise _database_unavailable() from error
    return BookingHistoryResponse.model_validate(history)


def _start_session(request: Request, response: Response, user_id: str) -> None:
    """Replace any existing login cookie with a new opaque session."""
    request.app.state.sessions.invalidate(request.cookies.get(SESSION_COOKIE))
    token = request.app.state.sessions.create(user_id)
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=False,
    )


@router.post("/api/accounts", response_model=AccountResponse, status_code=201)
def post_account(
    payload: AccountCreateRequest,
    request: Request,
    response: Response,
    connection: DatabaseConnection,
) -> AccountResponse:
    """Create an account and immediately start its login session."""
    try:
        account = create_account(
            connection,
            payload.username,
            payload.password,
            payload.email,
        )
    except DuplicateUsernameError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except AccountValidationError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except (sqlite3.DatabaseError, RuntimeError) as error:
        raise _database_unavailable() from error
    _start_session(request, response, account.user_id)
    return AccountResponse.model_validate(account)


@router.post("/api/auth/login", response_model=AccountResponse)
def post_login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    connection: DatabaseConnection,
) -> AccountResponse:
    """Authenticate credentials and start an opaque login session."""
    try:
        account = authenticate(connection, payload.username, payload.password)
    except AuthenticationError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    except sqlite3.DatabaseError as error:
        raise _database_unavailable() from error
    _start_session(request, response, account.user_id)
    return AccountResponse.model_validate(account)


@router.get("/api/auth/session", response_model=AccountResponse)
def get_session_account(
    user_id: AuthenticatedUserId,
    connection: DatabaseConnection,
) -> AccountResponse:
    """Return the password-free account for the current session."""
    try:
        account = get_account(connection, user_id)
    except RecordNotFoundError as error:
        raise HTTPException(status_code=401, detail="Log in to continue.") from error
    except sqlite3.DatabaseError as error:
        raise _database_unavailable() from error
    return AccountResponse.model_validate(account)


@router.post("/api/auth/logout", status_code=204)
def post_logout(request: Request) -> Response:
    """Invalidate the current session and clear its browser cookie."""
    request.app.state.sessions.invalidate(request.cookies.get(SESSION_COOKIE))
    response = Response(status_code=204)
    response.delete_cookie(SESSION_COOKIE, httponly=True, samesite="lax")
    return response


@router.post(
    "/api/bookings",
    response_model=BookingDetailResponse,
    status_code=201,
)
def post_booking(
    payload: BookingCreateRequest,
    user_id: AuthenticatedUserId,
    connection: DatabaseConnection,
) -> BookingDetailResponse:
    """Create and return a confirmed booking."""
    try:
        booking = create_booking(
            connection,
            user_id,
            payload.trip_id,
            search_query=payload.search_query,
        )
    except RecordNotFoundError as error:
        raise _not_found(error) from error
    except BookingValidationError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except (sqlite3.DatabaseError, RuntimeError) as error:
        raise _database_unavailable() from error
    return BookingDetailResponse.model_validate(booking)


@router.get(
    "/api/bookings/{booking_id}",
    response_model=BookingDetailResponse,
)
def get_booking_detail(
    booking_id: str,
    user_id: AuthenticatedUserId,
    connection: DatabaseConnection,
) -> BookingDetailResponse:
    """Retrieve one joined booking record."""
    try:
        booking = get_booking(connection, booking_id, user_id)
    except RecordNotFoundError as error:
        raise _not_found(error) from error
    except sqlite3.DatabaseError as error:
        raise _database_unavailable() from error
    return BookingDetailResponse.model_validate(booking)


@router.patch(
    "/api/bookings/{booking_id}",
    response_model=BookingDetailResponse,
)
def patch_booking_status(
    booking_id: str,
    payload: BookingStatusUpdateRequest,
    user_id: AuthenticatedUserId,
    connection: DatabaseConnection,
) -> BookingDetailResponse:
    """Update and return a booking's confirmed or cancelled status."""
    try:
        booking = update_booking_status(
            connection, booking_id, payload.status, user_id
        )
    except RecordNotFoundError as error:
        raise _not_found(error) from error
    except BookingValidationError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except sqlite3.DatabaseError as error:
        raise _database_unavailable() from error
    return BookingDetailResponse.model_validate(booking)


@router.delete("/api/bookings/{booking_id}", status_code=204)
def remove_booking(
    booking_id: str,
    user_id: AuthenticatedUserId,
    connection: DatabaseConnection,
) -> Response:
    """Permanently delete one booking."""
    try:
        delete_booking(connection, booking_id, user_id)
    except RecordNotFoundError as error:
        raise _not_found(error) from error
    except sqlite3.DatabaseError as error:
        raise _database_unavailable() from error
    return Response(status_code=204)
