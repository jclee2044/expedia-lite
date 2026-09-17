"""FastAPI routes that adapt HTTP requests to application controllers."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from backend.app.schemas import (
    BookingCreateRequest,
    BookingDetailResponse,
    BookingHistoryResponse,
    BookingStatusUpdateRequest,
    HotelSearchResponse,
    UserListResponse,
)
from backend.controllers.bookings import (
    create_booking,
    delete_booking,
    get_booking,
    update_booking_status,
)
from backend.controllers.database import connect_database
from backend.controllers.errors import (
    BookingValidationError,
    RecordNotFoundError,
    SearchValidationError,
)
from backend.controllers.search import search_hotel_stays
from backend.controllers.users import list_user_bookings, list_users

router = APIRouter()


def get_database(request: Request) -> Iterator[sqlite3.Connection]:
    """Provide one configured SQLite connection for an HTTP request."""
    connection = connect_database(request.app.state.database_path)
    try:
        yield connection
    finally:
        connection.close()


DatabaseConnection = Annotated[sqlite3.Connection, Depends(get_database)]


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
    name: str = Query(description="Case-insensitive partial hotel name"),
) -> HotelSearchResponse:
    """Search hotel names and return their joined available stays."""
    try:
        search = search_hotel_stays(name, connection)
    except sqlite3.DatabaseError as error:
        raise HTTPException(
            status_code=500,
            detail="The hotel data could not be loaded.",
        ) from error
    except SearchValidationError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return HotelSearchResponse.model_validate(search)


@router.get("/api/users", response_model=UserListResponse)
def get_users(connection: DatabaseConnection) -> UserListResponse:
    """List the synthetic travelers available for booking history."""
    try:
        return UserListResponse(users=list_users(connection))
    except sqlite3.DatabaseError as error:
        raise _database_unavailable() from error


@router.get(
    "/api/users/{user_id}/bookings",
    response_model=BookingHistoryResponse,
)
def get_user_booking_history(
    user_id: str,
    connection: DatabaseConnection,
) -> BookingHistoryResponse:
    """Retrieve one user's joined booking history."""
    try:
        history = list_user_bookings(connection, user_id)
    except RecordNotFoundError as error:
        raise _not_found(error) from error
    except sqlite3.DatabaseError as error:
        raise _database_unavailable() from error
    return BookingHistoryResponse.model_validate(history)


@router.post(
    "/api/bookings",
    response_model=BookingDetailResponse,
    status_code=201,
)
def post_booking(
    request: BookingCreateRequest,
    connection: DatabaseConnection,
) -> BookingDetailResponse:
    """Create and return a confirmed booking."""
    try:
        booking = create_booking(connection, request.user_id, request.trip_id)
    except RecordNotFoundError as error:
        raise _not_found(error) from error
    except (sqlite3.DatabaseError, RuntimeError) as error:
        raise _database_unavailable() from error
    return BookingDetailResponse.model_validate(booking)


@router.get(
    "/api/bookings/{booking_id}",
    response_model=BookingDetailResponse,
)
def get_booking_detail(
    booking_id: str,
    connection: DatabaseConnection,
) -> BookingDetailResponse:
    """Retrieve one joined booking record."""
    try:
        booking = get_booking(connection, booking_id)
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
    request: BookingStatusUpdateRequest,
    connection: DatabaseConnection,
) -> BookingDetailResponse:
    """Update and return a booking's confirmed or cancelled status."""
    try:
        booking = update_booking_status(connection, booking_id, request.status)
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
    connection: DatabaseConnection,
) -> Response:
    """Permanently delete one booking."""
    try:
        delete_booking(connection, booking_id)
    except RecordNotFoundError as error:
        raise _not_found(error) from error
    except sqlite3.DatabaseError as error:
        raise _database_unavailable() from error
    return Response(status_code=204)
