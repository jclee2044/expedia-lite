"""Framework-free checked facts returned by saved-hotel retrieval."""

from dataclasses import dataclass


@dataclass(frozen=True)
class StayRequest:
    """ZIP and dates resolved by backend input handling, never by proposed SQL."""

    postcode: str
    check_in: str
    check_out: str


@dataclass(frozen=True)
class VerifiedNight:
    stay_date: str
    nightly_rate_cents: int
    rooms_available: int


@dataclass(frozen=True)
class VerifiedStay:
    hotel_id: str
    name: str | None
    address: str | None
    postcode: str
    nights: tuple[VerifiedNight, ...]
    total_cents: int


@dataclass(frozen=True)
class RetrievalResult:
    """Only complete, available stays appear in matches.

    Candidate IDs are the bounded output of proposed SQL. Incomplete and
    unavailable IDs are checked by trusted backend SQL and must not be quoted
    as bookable stays. All rates and room counts are simulated course data.
    """

    candidate_ids: tuple[str, ...]
    matches: tuple[VerifiedStay, ...]
    incomplete_ids: tuple[str, ...]
    unavailable_ids: tuple[str, ...]
    saved_hotel_count: int
