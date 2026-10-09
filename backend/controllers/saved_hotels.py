"""Persist provider hotels and ZIP context separately from Assignment 1 data."""

from __future__ import annotations

import sqlite3

from backend.controllers.errors import RecordNotFoundError
from backend.models import (
    DemoHotelNight,
    ExternalHotel,
    PostcodeLocation,
    SavedHotel,
    SavedHotelSearch,
)

DEMO_STAY_DATES = tuple(f"2026-10-{day:02d}" for day in range(10, 15))


def save_provider_hotel(
    connection: sqlite3.Connection,
    hotel: ExternalHotel,
    center: PostcodeLocation,
) -> None:
    """Save a provider ID, its searched ZIP, and missing demo nights atomically."""
    try:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            """
            INSERT INTO saved_hotels (hotel_id, name, address, latitude, longitude)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(hotel_id) DO NOTHING
            """,
            (hotel.place_id, hotel.name, hotel.address, hotel.latitude, hotel.longitude),
        )
        connection.execute(
            """
            INSERT INTO saved_hotel_zips (
                hotel_id, postcode, country_code, latitude, longitude, locality
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(hotel_id, postcode) DO NOTHING
            """,
            (
                hotel.place_id, center.postcode, center.country_code,
                center.latitude, center.longitude, center.locality,
            ),
        )
        connection.executemany(
            """
            INSERT INTO demo_hotel_nights (hotel_id, stay_date)
            VALUES (?, ?)
            ON CONFLICT(hotel_id, stay_date) DO NOTHING
            """,
            [(hotel.place_id, stay_date) for stay_date in DEMO_STAY_DATES],
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def list_saved_hotels(connection: sqlite3.Connection, postcode: str) -> SavedHotelSearch:
    """Read ZIP-specific saved places and all globally saved provider IDs."""
    rows = connection.execute(
        """
        SELECT h.hotel_id, h.name, h.address, h.latitude AS hotel_latitude,
               h.longitude AS hotel_longitude, z.country_code,
               z.latitude AS center_latitude, z.longitude AS center_longitude,
               z.locality
        FROM saved_hotel_zips AS z
        JOIN saved_hotels AS h ON h.hotel_id = z.hotel_id
        WHERE z.postcode = ?
        ORDER BY h.hotel_id
        """,
        (postcode,),
    ).fetchall()
    saved_place_ids = [
        row["hotel_id"] for row in connection.execute(
            "SELECT hotel_id FROM saved_hotels ORDER BY hotel_id"
        ).fetchall()
    ]
    center = None
    if rows:
        first = rows[0]
        center = PostcodeLocation(
            postcode=postcode,
            country_code=first["country_code"],
            latitude=first["center_latitude"],
            longitude=first["center_longitude"],
            locality=first["locality"],
        )
    hotels = []
    for row in rows:
        night_rows = connection.execute(
            """
            SELECT stay_date, nightly_rate_cents, rooms_available
            FROM demo_hotel_nights WHERE hotel_id = ? ORDER BY stay_date
            """,
            (row["hotel_id"],),
        ).fetchall()
        hotels.append(SavedHotel(
            place_id=row["hotel_id"],
            name=row["name"],
            address=row["address"],
            latitude=row["hotel_latitude"],
            longitude=row["hotel_longitude"],
            nights=[DemoHotelNight(**dict(night)) for night in night_rows],
        ))
    return SavedHotelSearch(
        center=center, hotels=hotels, saved_place_ids=saved_place_ids
    )


def delete_saved_hotel(connection: sqlite3.Connection, hotel_id: str) -> None:
    """Delete one provider hotel, its ZIP links, and nights in one transaction."""
    try:
        connection.execute("BEGIN IMMEDIATE")
        if connection.execute(
            "SELECT 1 FROM saved_hotels WHERE hotel_id = ?", (hotel_id,)
        ).fetchone() is None:
            raise RecordNotFoundError("saved hotel", hotel_id)
        connection.execute("DELETE FROM demo_hotel_nights WHERE hotel_id = ?", (hotel_id,))
        connection.execute("DELETE FROM saved_hotel_zips WHERE hotel_id = ?", (hotel_id,))
        connection.execute("DELETE FROM saved_hotels WHERE hotel_id = ?", (hotel_id,))
        connection.commit()
    except Exception:
        connection.rollback()
        raise
