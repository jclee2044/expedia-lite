"""Validate supplied CSV files and seed a new SQLite database once."""

from __future__ import annotations

import csv
import re
import sqlite3
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import cast

from backend.models import Booking, BookingStatus, Hotel, Trip, User

SEED_VERSION = "1"
VALID_BOOKING_STATUSES = {"confirmed", "cancelled"}
DOMAIN_TABLES = ("hotels", "trips", "users", "bookings")


class SeedDataError(ValueError):
    """Raised when the supplied CSV files cannot form valid seed data."""


class SeedStateError(RuntimeError):
    """Raised when existing database state cannot be seeded safely."""


@dataclass(frozen=True)
class SeedData:
    """Validated entity objects ready for initial persistence."""

    hotels: list[Hotel]
    trips: list[Trip]
    users: list[User]
    bookings: list[Booking]


def _read_rows(path: Path, required_columns: set[str]) -> list[dict[str, str]]:
    try:
        with path.open(newline="", encoding="utf-8-sig") as csv_file:
            reader = csv.DictReader(csv_file)
            fieldnames = set(reader.fieldnames or [])
            missing_columns = required_columns - fieldnames
            if missing_columns:
                missing = ", ".join(sorted(missing_columns))
                raise SeedDataError(f"{path.name} is missing columns: {missing}")
            return [dict(row) for row in reader]
    except OSError as error:
        raise SeedDataError(f"Could not read {path}") from error


def _required_text(row: dict[str, str], column: str, filename: str) -> str:
    value = (row.get(column) or "").strip()
    if not value:
        raise SeedDataError(f"{filename} contains a blank {column}")
    return value


def _record_id(
    row: dict[str, str], column: str, prefix: str, filename: str
) -> str:
    value = _required_text(row, column, filename)
    if re.fullmatch(rf"{re.escape(prefix)}\d+", value) is None:
        raise SeedDataError(f"Invalid {column}: {value}")
    return value


def _unique_id(value: str, seen: set[str], column: str) -> None:
    if value in seen:
        raise SeedDataError(f"Duplicate {column}: {value}")
    seen.add(value)


def _iso_date(value: str, label: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise SeedDataError(f"Invalid date for {label}") from error


def _rate_in_cents(value: str, hotel_id: str) -> int:
    try:
        rate = Decimal(value)
    except InvalidOperation as error:
        raise SeedDataError(
            f"Invalid nightly rate for hotel_id {hotel_id}"
        ) from error
    if not rate.is_finite() or rate < 0:
        raise SeedDataError(f"Invalid nightly rate for hotel_id {hotel_id}")

    cents = rate * 100
    if cents != cents.to_integral_value():
        raise SeedDataError(
            f"Nightly rate has more than two decimals for hotel_id {hotel_id}"
        )
    return int(cents)


def load_seed_data(data_directory: Path) -> SeedData:
    """Load and validate all four related seed files without writing data."""
    hotel_rows = _read_rows(
        data_directory / "hotels.csv",
        {"hotel_id", "hotel_name", "city", "state", "nightly_rate_usd"},
    )
    trip_rows = _read_rows(
        data_directory / "trips.csv",
        {"trip_id", "hotel_id", "trip_name", "check_in", "check_out"},
    )
    user_rows = _read_rows(
        data_directory / "users.csv", {"user_id", "display_name"}
    )
    booking_rows = _read_rows(
        data_directory / "bookings.csv",
        {"booking_id", "user_id", "trip_id", "booked_on", "status"},
    )

    hotels: list[Hotel] = []
    hotel_ids: set[str] = set()
    for row in hotel_rows:
        hotel_id = _record_id(row, "hotel_id", "H", "hotels.csv")
        _unique_id(hotel_id, hotel_ids, "hotel_id")
        hotels.append(
            Hotel(
                hotel_id=hotel_id,
                hotel_name=_required_text(row, "hotel_name", "hotels.csv"),
                city=_required_text(row, "city", "hotels.csv"),
                state=_required_text(row, "state", "hotels.csv"),
                nightly_rate_cents=_rate_in_cents(
                    _required_text(row, "nightly_rate_usd", "hotels.csv"),
                    hotel_id,
                ),
            )
        )

    trips: list[Trip] = []
    trip_ids: set[str] = set()
    for row in trip_rows:
        trip_id = _record_id(row, "trip_id", "T", "trips.csv")
        _unique_id(trip_id, trip_ids, "trip_id")
        hotel_id = _record_id(row, "hotel_id", "H", "trips.csv")
        if hotel_id not in hotel_ids:
            raise SeedDataError(
                f"trip_id {trip_id} references unknown hotel_id {hotel_id}"
            )
        check_in = _iso_date(
            _required_text(row, "check_in", "trips.csv"), f"trip_id {trip_id}"
        )
        check_out = _iso_date(
            _required_text(row, "check_out", "trips.csv"), f"trip_id {trip_id}"
        )
        if check_out <= check_in:
            raise SeedDataError(
                f"check_out must be after check_in for trip_id {trip_id}"
            )
        trips.append(
            Trip(
                trip_id=trip_id,
                hotel_id=hotel_id,
                trip_name=_required_text(row, "trip_name", "trips.csv"),
                check_in=check_in,
                check_out=check_out,
            )
        )

    users: list[User] = []
    user_ids: set[str] = set()
    for row in user_rows:
        user_id = _record_id(row, "user_id", "U", "users.csv")
        _unique_id(user_id, user_ids, "user_id")
        users.append(
            User(
                user_id=user_id,
                display_name=_required_text(row, "display_name", "users.csv"),
            )
        )

    bookings: list[Booking] = []
    booking_ids: set[str] = set()
    for row in booking_rows:
        booking_id = _record_id(row, "booking_id", "B", "bookings.csv")
        _unique_id(booking_id, booking_ids, "booking_id")
        user_id = _record_id(row, "user_id", "U", "bookings.csv")
        trip_id = _record_id(row, "trip_id", "T", "bookings.csv")
        if user_id not in user_ids:
            raise SeedDataError(
                f"booking_id {booking_id} references unknown user_id {user_id}"
            )
        if trip_id not in trip_ids:
            raise SeedDataError(
                f"booking_id {booking_id} references unknown trip_id {trip_id}"
            )
        booked_on = _iso_date(
            _required_text(row, "booked_on", "bookings.csv"),
            f"booking_id {booking_id}",
        )
        status = _required_text(row, "status", "bookings.csv")
        if status not in VALID_BOOKING_STATUSES:
            raise SeedDataError(f"Invalid status for booking_id {booking_id}")
        bookings.append(
            Booking(
                booking_id=booking_id,
                user_id=user_id,
                trip_id=trip_id,
                booked_on=booked_on,
                status=cast(BookingStatus, status),
            )
        )

    return SeedData(hotels=hotels, trips=trips, users=users, bookings=bookings)


def _table_counts(connection: sqlite3.Connection) -> dict[str, int]:
    return {
        table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in DOMAIN_TABLES
    }


def _booking_suffix(booking_id: str) -> int:
    return int(booking_id[1:])


def seed_database(connection: sqlite3.Connection, data_directory: Path) -> bool:
    """Seed an empty schema exactly once, returning whether rows were added."""
    seed_row = connection.execute(
        "SELECT value FROM app_metadata WHERE key = 'seed_version'"
    ).fetchone()
    if seed_row is not None:
        if seed_row["value"] != SEED_VERSION:
            raise SeedStateError(
                f"Unsupported database seed version: {seed_row['value']}"
            )
        return False

    counts = _table_counts(connection)
    populated = {table: count for table, count in counts.items() if count}
    if populated:
        summary = ", ".join(
            f"{table}={count}" for table, count in populated.items()
        )
        raise SeedStateError(
            "Refusing to seed a database with unmarked existing data: " + summary
        )

    seed_data = load_seed_data(data_directory)
    greatest_booking_suffix = max(
        (_booking_suffix(booking.booking_id) for booking in seed_data.bookings),
        default=0,
    )

    try:
        connection.execute("BEGIN IMMEDIATE")
        connection.executemany(
            """
            INSERT INTO hotels (
                hotel_id, hotel_name, city, state, nightly_rate_cents
            ) VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    hotel.hotel_id,
                    hotel.hotel_name,
                    hotel.city,
                    hotel.state,
                    hotel.nightly_rate_cents,
                )
                for hotel in seed_data.hotels
            ],
        )
        connection.executemany(
            """
            INSERT INTO trips (
                trip_id, hotel_id, trip_name, check_in, check_out
            ) VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    trip.trip_id,
                    trip.hotel_id,
                    trip.trip_name,
                    trip.check_in.isoformat(),
                    trip.check_out.isoformat(),
                )
                for trip in seed_data.trips
            ],
        )
        connection.executemany(
            "INSERT INTO users (user_id, display_name) VALUES (?, ?)",
            [(user.user_id, user.display_name) for user in seed_data.users],
        )
        connection.executemany(
            """
            INSERT INTO bookings (
                booking_id, user_id, trip_id, booked_on, status
            ) VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    booking.booking_id,
                    booking.user_id,
                    booking.trip_id,
                    booking.booked_on.isoformat(),
                    booking.status,
                )
                for booking in seed_data.bookings
            ],
        )
        connection.execute(
            "INSERT INTO id_counters (entity, last_value) VALUES ('booking', ?)",
            (greatest_booking_suffix,),
        )
        connection.execute(
            "INSERT INTO app_metadata (key, value) VALUES ('seed_version', ?)",
            (SEED_VERSION,),
        )
        connection.commit()
    except sqlite3.DatabaseError as error:
        connection.rollback()
        raise SeedStateError("Could not seed the SQLite database.") from error

    return True
