"""Saved provider hotel API and SQLite mutation checks use temporary databases."""

from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.controllers.database import connect_database, initialize_database

DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"


def payload(place_id: str = "provider:ABC", postcode: str = "16802") -> dict:
    return {
        "hotel": {
            "place_id": place_id,
            "name": "Scholar Hotel",
            "address": "205 East Beaver Avenue",
            "latitude": 40.7946,
            "longitude": -77.8590,
        },
        "center": {
            "postcode": postcode,
            "country_code": "us",
            "latitude": 40.8031,
            "longitude": -77.8613,
            "locality": "State College",
        },
    }


def test_save_lookup_repeat_and_delete_preserve_unrelated_records(tmp_path: Path) -> None:
    database_path = tmp_path / "expedia.sqlite3"
    with TestClient(create_app(database_path, DATA_DIRECTORY)) as client:
        empty = client.get("/api/saved-hotels", params={"postcode": "16802"})
        assert empty.status_code == 200
        assert empty.json() == {"center": None, "hotels": [], "saved_place_ids": []}

        assert client.post("/api/saved-hotels", json=payload()).json() == {
            "place_id": "provider:ABC"
        }
        saved = client.get("/api/saved-hotels", params={"postcode": "16802"}).json()
        assert saved["center"] == payload()["center"]
        assert saved["saved_place_ids"] == ["provider:ABC"]
        assert saved["hotels"] == [{
            **payload()["hotel"],
            "nights": [
                {"stay_date": f"2026-10-{day:02d}", "nightly_rate_cents": 10000,
                 "rooms_available": 20}
                for day in range(10, 15)
            ],
        }]

        connection = connect_database(database_path)
        try:
            connection.execute(
                """
                UPDATE demo_hotel_nights
                SET nightly_rate_cents = 12500, rooms_available = 3
                WHERE hotel_id = 'provider:ABC' AND stay_date = '2026-10-11'
                """
            )
            connection.commit()
        finally:
            connection.close()

        repeat = payload(postcode="16803")
        repeat["hotel"]["name"] = "Changed provider name"
        assert client.post("/api/saved-hotels", json=repeat).status_code == 200
        assert client.post("/api/saved-hotels", json=repeat).status_code == 200
        other = client.get("/api/saved-hotels", params={"postcode": "16803"}).json()
        assert len(other["hotels"]) == 1
        assert other["hotels"][0]["name"] == "Scholar Hotel"
        assert other["hotels"][0]["nights"][1] == {
            "stay_date": "2026-10-11", "nightly_rate_cents": 12500,
            "rooms_available": 3,
        }
        original_zip = client.get("/api/saved-hotels", params={"postcode": "16802"}).json()
        assert original_zip["hotels"] == other["hotels"]
        assert len(original_zip["hotels"][0]["nights"]) == 5
        assert client.post("/api/saved-hotels", json=payload("provider:OTHER")).status_code == 200

        assert client.delete("/api/saved-hotels/provider%3AABC").status_code == 204
        assert client.delete("/api/saved-hotels/provider%3AABC").status_code == 404
        after = client.get("/api/saved-hotels", params={"postcode": "16803"}).json()
        assert after == {"center": None, "hotels": [], "saved_place_ids": ["provider:OTHER"]}

    connection = connect_database(database_path)
    try:
        assert connection.execute(
            "SELECT COUNT(*) FROM saved_hotels WHERE hotel_id = 'provider:ABC'"
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT COUNT(*) FROM saved_hotel_zips WHERE hotel_id = 'provider:ABC'"
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT COUNT(*) FROM demo_hotel_nights WHERE hotel_id = 'provider:ABC'"
        ).fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM saved_hotels").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM hotels").fetchone()[0] == 8
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        connection.close()


def test_saved_hotel_validation_and_missing_delete(tmp_path: Path) -> None:
    with TestClient(create_app(tmp_path / "expedia.sqlite3", DATA_DIRECTORY)) as client:
        assert client.get("/api/saved-hotels", params={"postcode": "bad"}).status_code == 422
        assert client.delete("/api/saved-hotels/unknown").status_code == 404
        invalid = payload()
        invalid["hotel"]["latitude"] = 91
        assert client.post("/api/saved-hotels", json=invalid).status_code == 422
        invalid = payload()
        invalid["center"]["postcode"] = "1234"
        assert client.post("/api/saved-hotels", json=invalid).status_code == 422
        assert client.post("/api/saved-hotels", json=payload("provider:ABC/1")).status_code == 200
        assert client.delete("/api/saved-hotels/provider%3AABC%2F1").status_code == 204


def test_version_five_migration_preserves_saved_hotel_and_nights(tmp_path: Path) -> None:
    database_path = tmp_path / "expedia.sqlite3"
    initialize_database(database_path, DATA_DIRECTORY)
    connection = connect_database(database_path)
    try:
        connection.execute(
            "INSERT INTO saved_hotels VALUES ('provider:ABC', NULL, NULL, 40, -77)"
        )
        connection.execute(
            "INSERT INTO demo_hotel_nights (hotel_id, stay_date) "
            "VALUES ('provider:ABC', '2026-10-10')"
        )
        connection.execute("DROP TABLE saved_hotel_zips")
        connection.execute(
            "UPDATE app_metadata SET value = '5' WHERE key = 'schema_version'"
        )
        connection.commit()
    finally:
        connection.close()

    assert initialize_database(database_path, DATA_DIRECTORY) is False
    assert initialize_database(database_path, DATA_DIRECTORY) is False
    migrated = connect_database(database_path)
    try:
        assert migrated.execute(
            "SELECT value FROM app_metadata WHERE key = 'schema_version'"
        ).fetchone()[0] == "7"
        assert migrated.execute("SELECT COUNT(*) FROM saved_hotels").fetchone()[0] == 1
        assert migrated.execute("SELECT COUNT(*) FROM demo_hotel_nights").fetchone()[0] == 1
        assert migrated.execute("SELECT COUNT(*) FROM saved_hotel_zips").fetchone()[0] == 0
    finally:
        migrated.close()
