"""Framework-free hotel search and CSV joining logic."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path


class DataValidationError(ValueError):
    """Raised when the supplied CSV data cannot form valid hotel stays."""


@dataclass(frozen=True)
class Hotel:
    hotel_id: str
    hotel_name: str
    city: str
    state: str
    nightly_rate_usd: Decimal


@dataclass(frozen=True)
class Trip:
    trip_id: str
    hotel_id: str
    trip_name: str
    check_in: date
    check_out: date


@dataclass(frozen=True)
class HotelStay:
    hotel_id: str
    hotel_name: str
    city: str
    state: str
    trip_id: str
    trip_name: str
    check_in: date
    check_out: date
    nights: int
    nightly_rate_usd: Decimal
    stay_price_usd: Decimal


@dataclass(frozen=True)
class HotelSearch:
    query: str
    hotel_count: int
    results: list[HotelStay]


def _read_rows(path: Path, required_columns: set[str]) -> list[dict[str, str]]:
    try:
        with path.open(newline="", encoding="utf-8-sig") as csv_file:
            reader = csv.DictReader(csv_file)
            fieldnames = set(reader.fieldnames or [])
            missing_columns = required_columns - fieldnames
            if missing_columns:
                missing = ", ".join(sorted(missing_columns))
                raise DataValidationError(f"{path.name} is missing columns: {missing}")
            return [dict(row) for row in reader]
    except OSError as error:
        raise DataValidationError(f"Could not read {path}") from error


def load_hotels(path: Path) -> dict[str, Hotel]:
    """Load hotels indexed by their unique hotel ID."""
    rows = _read_rows(
        path,
        {"hotel_id", "hotel_name", "city", "state", "nightly_rate_usd"},
    )
    hotels: dict[str, Hotel] = {}

    for row in rows:
        hotel_id = row["hotel_id"].strip()
        if not hotel_id:
            raise DataValidationError("hotels.csv contains a blank hotel_id")
        if hotel_id in hotels:
            raise DataValidationError(f"Duplicate hotel_id: {hotel_id}")

        try:
            nightly_rate = Decimal(row["nightly_rate_usd"])
        except InvalidOperation as error:
            raise DataValidationError(
                f"Invalid nightly rate for hotel_id {hotel_id}"
            ) from error
        if nightly_rate < 0:
            raise DataValidationError(
                f"Nightly rate cannot be negative for hotel_id {hotel_id}"
            )

        hotels[hotel_id] = Hotel(
            hotel_id=hotel_id,
            hotel_name=row["hotel_name"].strip(),
            city=row["city"].strip(),
            state=row["state"].strip(),
            nightly_rate_usd=nightly_rate,
        )

    return hotels


def load_trips(path: Path) -> list[Trip]:
    """Load offered hotel stays from the trips CSV."""
    rows = _read_rows(
        path,
        {"trip_id", "hotel_id", "trip_name", "check_in", "check_out"},
    )
    trips: list[Trip] = []
    seen_trip_ids: set[str] = set()

    for row in rows:
        trip_id = row["trip_id"].strip()
        if not trip_id:
            raise DataValidationError("trips.csv contains a blank trip_id")
        if trip_id in seen_trip_ids:
            raise DataValidationError(f"Duplicate trip_id: {trip_id}")

        try:
            check_in = date.fromisoformat(row["check_in"])
            check_out = date.fromisoformat(row["check_out"])
        except ValueError as error:
            raise DataValidationError(f"Invalid dates for trip_id {trip_id}") from error
        if check_out <= check_in:
            raise DataValidationError(
                f"check_out must be after check_in for trip_id {trip_id}"
            )

        trips.append(
            Trip(
                trip_id=trip_id,
                hotel_id=row["hotel_id"].strip(),
                trip_name=row["trip_name"].strip(),
                check_in=check_in,
                check_out=check_out,
            )
        )
        seen_trip_ids.add(trip_id)

    return trips


def search_hotel_stays(
    query: str,
    hotels_path: Path,
    trips_path: Path,
) -> HotelSearch:
    """Return stays whose joined hotel name contains the normalized query."""
    normalized_query = query.strip()
    if not normalized_query:
        raise ValueError("Enter a hotel name.")

    hotels = load_hotels(hotels_path)
    trips = load_trips(trips_path)
    matching_hotel_ids = {
        hotel.hotel_id
        for hotel in hotels.values()
        if normalized_query.casefold() in hotel.hotel_name.casefold()
    }

    results: list[HotelStay] = []
    for trip in trips:
        hotel = hotels.get(trip.hotel_id)
        if hotel is None:
            raise DataValidationError(
                f"trip_id {trip.trip_id} references unknown hotel_id {trip.hotel_id}"
            )
        if trip.hotel_id not in matching_hotel_ids:
            continue

        nights = (trip.check_out - trip.check_in).days
        results.append(
            HotelStay(
                hotel_id=hotel.hotel_id,
                hotel_name=hotel.hotel_name,
                city=hotel.city,
                state=hotel.state,
                trip_id=trip.trip_id,
                trip_name=trip.trip_name,
                check_in=trip.check_in,
                check_out=trip.check_out,
                nights=nights,
                nightly_rate_usd=hotel.nightly_rate_usd,
                stay_price_usd=hotel.nightly_rate_usd * nights,
            )
        )

    return HotelSearch(
        query=normalized_query,
        hotel_count=len({result.hotel_id for result in results}),
        results=results,
    )
