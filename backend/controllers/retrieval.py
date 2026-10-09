"""Bound and independently verify model-proposed saved-hotel SELECT queries."""

from __future__ import annotations

import re
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from time import monotonic
from typing import Mapping

from backend.models.retrieval import RetrievalResult, StayRequest, VerifiedNight, VerifiedStay

ALLOWED_TABLES = frozenset({"saved_hotels", "saved_hotel_zips", "demo_hotel_nights"})
REQUIRED_BINDS = frozenset({"postcode", "check_in", "check_out"})
MAX_CANDIDATES = 50
MAX_STAY_NIGHTS = 14
MAX_SQL_LENGTH = 4000
QUERY_TIMEOUT_SECONDS = 0.25
_BIND_PATTERN = re.compile(r":([A-Za-z_][A-Za-z_0-9]*)")
_POSTCODE_PATTERN = re.compile(r"[0-9]{5}\Z")


class RetrievalRejectedError(ValueError):
    """A proposed query, its parameters, or its result violates the contract."""


def _parse_day(value: str) -> date:
    try:
        parsed = date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise RetrievalRejectedError("Stay dates must be ISO calendar dates.") from exc
    if parsed.isoformat() != value:
        raise RetrievalRejectedError("Stay dates must be ISO calendar dates.")
    return parsed


def _validate_proposal(
    sql: str, params: Mapping[str, str], request: StayRequest
) -> tuple[str, date, date]:
    if not isinstance(sql, str) or not (0 < len(sql) <= MAX_SQL_LENGTH):
        raise RetrievalRejectedError("Proposed SQL length is invalid.")
    if not re.match(r"\A\s*SELECT\b", sql, re.IGNORECASE):
        raise RetrievalRejectedError("Proposed SQL must start with SELECT.")
    if any(token in sql for token in (";", "--", "/*", "*/", "'", '"', "`", "?", "$", "@")):
        raise RetrievalRejectedError("Proposed SQL uses unsupported syntax.")
    if set(_BIND_PATTERN.findall(sql)) != REQUIRED_BINDS:
        raise RetrievalRejectedError("Proposed SQL must use the three named binds.")
    if not isinstance(params, Mapping) or set(params) != REQUIRED_BINDS or not all(
        isinstance(value, str) for value in params.values()
    ):
        raise RetrievalRejectedError("Proposed parameters are invalid.")
    if not isinstance(request, StayRequest):
        raise RetrievalRejectedError("Trusted stay request is required.")
    trusted_params = {
        "postcode": request.postcode,
        "check_in": request.check_in,
        "check_out": request.check_out,
    }
    if not all(isinstance(value, str) for value in trusted_params.values()):
        raise RetrievalRejectedError("Trusted stay request is invalid.")
    if dict(params) != trusted_params:
        raise RetrievalRejectedError("Proposed parameters differ from the requested stay.")
    postcode = request.postcode
    if not _POSTCODE_PATTERN.fullmatch(postcode):
        raise RetrievalRejectedError("Postcode must be five ASCII digits.")
    check_in = _parse_day(request.check_in)
    check_out = _parse_day(request.check_out)
    nights = (check_out - check_in).days
    if not 1 <= nights <= MAX_STAY_NIGHTS:
        raise RetrievalRejectedError("Stay must contain one to fourteen nights.")
    return postcode, check_in, check_out


def _read_only_connection(database_path: Path) -> sqlite3.Connection:
    if not database_path.is_file():
        raise RetrievalRejectedError("Saved-hotel database is unavailable.")
    connection = sqlite3.connect(
        database_path.resolve().as_uri() + "?mode=ro",
        uri=True,
        timeout=QUERY_TIMEOUT_SECONDS,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    connection.execute("BEGIN")
    return connection


def _candidate_ids(
    connection: sqlite3.Connection, sql: str, params: Mapping[str, str]
) -> tuple[str, ...]:
    deadline = monotonic() + QUERY_TIMEOUT_SECONDS

    def authorize(action: int, first: str | None, _second: str | None,
                  _database: str | None, _source: str | None) -> int:
        if action == sqlite3.SQLITE_SELECT:
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_READ and first in ALLOWED_TABLES:
            return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY

    def timed_out() -> int:
        return int(monotonic() >= deadline)

    connection.set_authorizer(authorize)
    connection.set_progress_handler(timed_out, 100)
    try:
        cursor = connection.execute(sql, dict(params))
        if [column[0] for column in cursor.description] != ["hotel_id"]:
            raise RetrievalRejectedError("Proposed SQL must return only hotel_id.")
        rows = cursor.fetchmany(MAX_CANDIDATES + 1)
        if len(rows) > MAX_CANDIDATES:
            raise RetrievalRejectedError("Proposed SQL exceeded the row limit.")
        ids = tuple(row[0] for row in rows)
        if any(not isinstance(hotel_id, str) or not hotel_id for hotel_id in ids):
            raise RetrievalRejectedError("Proposed SQL returned invalid hotel IDs.")
        return tuple(dict.fromkeys(ids))
    except sqlite3.Error as exc:
        raise RetrievalRejectedError("Proposed SQL was rejected or timed out.") from exc
    finally:
        connection.set_authorizer(None)
        connection.set_progress_handler(None, 0)


def _verify_candidates(
    connection: sqlite3.Connection,
    candidate_ids: tuple[str, ...],
    postcode: str,
    check_in: date,
    check_out: date,
) -> RetrievalResult:
    requested_dates = tuple(
        (check_in + timedelta(days=offset)).isoformat()
        for offset in range((check_out - check_in).days)
    )
    matches: list[VerifiedStay] = []
    incomplete: list[str] = []
    unavailable: list[str] = []
    for hotel_id in candidate_ids:
        hotel = connection.execute(
            """
            SELECT h.hotel_id, h.name, h.address
            FROM saved_hotels AS h
            JOIN saved_hotel_zips AS z ON z.hotel_id = h.hotel_id
            WHERE h.hotel_id = ? AND z.postcode = ?
            """,
            (hotel_id, postcode),
        ).fetchone()
        if hotel is None:
            continue
        rows = connection.execute(
            """
            SELECT stay_date, nightly_rate_cents, rooms_available
            FROM demo_hotel_nights
            WHERE hotel_id = ? AND stay_date >= ? AND stay_date < ?
            ORDER BY stay_date
            """,
            (hotel_id, check_in.isoformat(), check_out.isoformat()),
        ).fetchall()
        by_date = {row["stay_date"]: row for row in rows}
        if any(day not in by_date for day in requested_dates):
            incomplete.append(hotel_id)
            continue
        if any(by_date[day]["rooms_available"] <= 0 for day in requested_dates):
            unavailable.append(hotel_id)
            continue
        nights = tuple(
            VerifiedNight(
                stay_date=day,
                nightly_rate_cents=by_date[day]["nightly_rate_cents"],
                rooms_available=by_date[day]["rooms_available"],
            )
            for day in requested_dates
        )
        matches.append(VerifiedStay(
            hotel_id=hotel_id,
            name=hotel["name"],
            address=hotel["address"],
            postcode=postcode,
            nights=nights,
            total_cents=sum(night.nightly_rate_cents for night in nights),
        ))
    matches.sort(key=lambda stay: (stay.total_cents, stay.hotel_id))
    saved_count = connection.execute(
        "SELECT COUNT(*) FROM saved_hotel_zips WHERE postcode = ?", (postcode,)
    ).fetchone()[0]
    return RetrievalResult(
        candidate_ids, tuple(matches), tuple(incomplete), tuple(unavailable), saved_count
    )


def retrieve_saved_stays(
    database_path: Path,
    proposed_sql: str,
    proposed_params: Mapping[str, str],
    request: StayRequest,
) -> RetrievalResult:
    """Execute a bounded candidate SELECT, then verify facts with trusted SQL.

    The proposed query may only return hotel IDs. It never determines price,
    availability, ZIP eligibility, or totals. No write connection is opened.
    """
    postcode, check_in, check_out = _validate_proposal(proposed_sql, proposed_params, request)
    trusted_params = {
        "postcode": request.postcode,
        "check_in": request.check_in,
        "check_out": request.check_out,
    }
    connection = _read_only_connection(database_path)
    try:
        candidate_ids = _candidate_ids(connection, proposed_sql, trusted_params)
        return _verify_candidates(connection, candidate_ids, postcode, check_in, check_out)
    finally:
        connection.rollback()
        connection.close()
