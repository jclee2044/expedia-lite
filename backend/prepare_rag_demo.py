"""Create a new, ignored SQLite database for the Part 2 synthetic RAG demo."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.controllers.database import connect_database, initialize_database

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_DIRECTORY = PROJECT_ROOT / "backend" / "db"
FIXTURE_PATH = PROJECT_ROOT / "docs" / "part2-rag-fixture.json"
DATA_DIRECTORY = PROJECT_ROOT / "data"


def prepare_demo_database(output: Path) -> None:
    """Seed only a new database inside backend/db from the reviewed fixture."""
    target = output.resolve()
    if target.parent != DEMO_DIRECTORY.resolve() or target.suffix != ".sqlite3":
        raise ValueError("Choose a .sqlite3 output directly inside backend/db.")
    if target.exists():
        raise FileExistsError(f"Output already exists: {target}")

    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    postcode = fixture["postcode"]
    latitude = fixture["latitude"]
    longitude = fixture["longitude"]
    hotels = fixture["hotels"]

    initialize_database(target, DATA_DIRECTORY)
    connection = connect_database(target)
    try:
        for hotel in hotels:
            hotel_id = hotel["hotel_id"]
            connection.execute(
                "INSERT INTO saved_hotels (hotel_id, name, address, latitude, longitude) "
                "VALUES (?, ?, NULL, ?, ?)",
                (hotel_id, hotel["name"], latitude, longitude),
            )
            connection.execute(
                "INSERT INTO saved_hotel_zips "
                "(hotel_id, postcode, country_code, latitude, longitude, locality) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    hotel_id, postcode, fixture["country_code"],
                    latitude, longitude, fixture["locality"],
                ),
            )
            for night in hotel["nights"]:
                connection.execute(
                    "INSERT INTO demo_hotel_nights "
                    "(hotel_id, stay_date, nightly_rate_cents, rooms_available) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        hotel_id, night["stay_date"],
                        night["nightly_rate_cents"], night["rooms_available"],
                    ),
                )
        if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
            raise ValueError("Synthetic fixture violates a database relationship.")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="new backend/db/*.sqlite3 path")
    args = parser.parse_args()
    prepare_demo_database(args.output)
    print(f"Created synthetic RAG demo database: {args.output}")


if __name__ == "__main__":
    main()
