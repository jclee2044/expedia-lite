"""FastAPI routes that adapt HTTP requests to application controllers."""

from __future__ import annotations

import sqlite3
from collections.abc import AsyncIterator, Iterator
from contextlib import aclosing
from typing import Annotated
import json

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse

from backend.app.schemas import (
    AccountCreateRequest,
    AccountResponse,
    BookingCreateRequest,
    BookingDetailResponse,
    BookingHistoryResponse,
    BookingStatusUpdateRequest,
    ChatHistoryResponse,
    ChatStreamRequest,
    HealthResponse,
    HotelSearchResponse,
    LoginRequest,
    NearbyHotelSearchResponse,
    PostcodeLocationResponse,
    SavedHotelCreateRequest,
    SavedHotelMutationResponse,
    SavedHotelSearchResponse,
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
    GeoapifyConfigurationError,
    GeoapifyRequestError,
    PostcodeNotFoundError,
    RecordNotFoundError,
    SearchValidationError,
)
from backend.controllers.geocoding import lookup_us_postcode
from backend.controllers.chat_history import ConversationNotFoundError, load_history
from backend.controllers.rag_chat import stream_rag_answer
from backend.controllers.places import search_nearby_hotels
from backend.controllers.search import search_hotel_stays
from backend.controllers.saved_hotels import (
    delete_saved_hotel,
    list_saved_hotels,
    save_provider_hotel,
)
from backend.controllers.users import list_user_bookings
from backend.models import ExternalHotel, PostcodeLocation

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


def _chat_event(kind: str, payload: dict[str, str]) -> str:
    return f"event: {kind}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.post("/api/chat/stream")
async def post_chat_stream(payload: ChatStreamRequest, request: Request) -> StreamingResponse:
    """Stream the checked two-call hotel answer and its conversation ID."""

    async def events() -> AsyncIterator[str]:
        try:
            stream = stream_rag_answer(
                request.app.state.database_path, payload.question.strip(),
                str(payload.conversation_id) if payload.conversation_id else None,
                request.app.state.assistant_prompt,
            )
            async with aclosing(stream):
                async for event in stream:
                    if await request.is_disconnected():
                        return
                    yield _chat_event(event.kind, event.payload)
        except ConversationNotFoundError as error:
            yield _chat_event("error", {"message": str(error)})

    return StreamingResponse(
        events(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/api/chat/history", response_model=ChatHistoryResponse)
def get_chat_history(request: Request, conversation_id: str = Query(pattern=r"^[0-9a-fA-F-]{36}$")) -> ChatHistoryResponse:
    """Restore saved messages after a browser refresh or backend restart."""
    try:
        history = load_history(request.app.state.database_path, conversation_id)
    except ConversationNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return ChatHistoryResponse.model_validate(history)


@router.get("/api/health", response_model=HealthResponse)
def get_health(request: Request) -> HealthResponse:
    """Report service health without exposing configuration values."""
    key_status = (
        "key is configured"
        if request.app.state.geoapify_key_configured
        else "key is not configured"
    )
    return HealthResponse(status="ok", geoapify_api_key=key_status)


@router.get("/api/demo/zip-location", response_model=PostcodeLocationResponse)
def get_demo_zip_location() -> PostcodeLocationResponse:
    """Resolve the fixed classroom demonstration ZIP through the controller."""
    return _resolve_zip_location("16802")


@router.get("/api/zip-location", response_model=PostcodeLocationResponse)
def get_zip_location(
    postcode: str = Query(pattern=r"^[0-9]{5}$", description="Five-digit U.S. ZIP code"),
) -> PostcodeLocationResponse:
    """Resolve a validated U.S. ZIP supplied by the caller."""
    return _resolve_zip_location(postcode)


@router.get("/api/hotels/nearby", response_model=NearbyHotelSearchResponse)
def get_nearby_hotels(
    postcode: str = Query(pattern=r"^[0-9]{5}$", description="Five-digit U.S. ZIP code"),
) -> NearbyHotelSearchResponse:
    """Find Geoapify hotels within 5 km of the resolved U.S. ZIP point."""
    try:
        search = search_nearby_hotels(postcode)
    except GeoapifyConfigurationError as error:
        raise HTTPException(status_code=503, detail="Hotel location service is not configured.") from error
    except PostcodeNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"ZIP code {postcode} could not be resolved.") from error
    except GeoapifyRequestError as error:
        raise HTTPException(status_code=502, detail="Nearby hotel provider is unavailable.") from error
    return NearbyHotelSearchResponse.model_validate(search)


@router.get("/api/saved-hotels", response_model=SavedHotelSearchResponse)
def get_saved_hotels(
    connection: DatabaseConnection,
    postcode: str = Query(pattern=r"^[0-9]{5}$", description="Five-digit U.S. ZIP code"),
) -> SavedHotelSearchResponse:
    """Return saved hotels for a ZIP and all saved provider IDs."""
    try:
        result = list_saved_hotels(connection, postcode)
    except sqlite3.DatabaseError as error:
        raise HTTPException(status_code=500, detail="Saved hotels could not be loaded.") from error
    return SavedHotelSearchResponse.model_validate(result)


@router.post("/api/saved-hotels", response_model=SavedHotelMutationResponse)
def post_saved_hotel(
    payload: SavedHotelCreateRequest,
    connection: DatabaseConnection,
) -> SavedHotelMutationResponse:
    """Save a provider place with its ZIP context and fictional demo nights."""
    try:
        save_provider_hotel(
            connection,
            ExternalHotel(**payload.hotel.model_dump()),
            PostcodeLocation(**payload.center.model_dump()),
        )
    except sqlite3.DatabaseError as error:
        raise HTTPException(status_code=500, detail="Hotel could not be saved locally.") from error
    return SavedHotelMutationResponse(place_id=payload.hotel.place_id)


@router.delete("/api/saved-hotels/{hotel_id:path}", status_code=204)
def remove_saved_hotel(hotel_id: str, connection: DatabaseConnection) -> Response:
    """Remove a provider place and its ZIP and nightly records."""
    try:
        delete_saved_hotel(connection, hotel_id)
    except RecordNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except sqlite3.DatabaseError as error:
        raise HTTPException(status_code=500, detail="Hotel could not be removed locally.") from error
    return Response(status_code=204)


def _resolve_zip_location(postcode: str) -> PostcodeLocationResponse:
    try:
        location = lookup_us_postcode(postcode)
    except GeoapifyConfigurationError as error:
        raise HTTPException(
            status_code=503,
            detail="ZIP location service is not configured.",
        ) from error
    except PostcodeNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=f"ZIP code {postcode} could not be resolved.",
        ) from error
    except GeoapifyRequestError as error:
        raise HTTPException(
            status_code=502,
            detail="ZIP location provider is unavailable.",
        ) from error
    return PostcodeLocationResponse.model_validate(location)


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
