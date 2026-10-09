"""Synthetic fixture and rejection checks for read-only retrieval."""

from pathlib import Path

import pytest

from backend.controllers.database import connect_database, initialize_database
from backend.controllers.retrieval import RetrievalRejectedError, retrieve_saved_stays
from backend.controllers import retrieval
from backend.models.retrieval import RetrievalResult, StayRequest

DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"
PROPOSAL = """
SELECT DISTINCT h.hotel_id AS hotel_id
FROM saved_hotels AS h
JOIN saved_hotel_zips AS z ON z.hotel_id = h.hotel_id
LEFT JOIN demo_hotel_nights AS n
  ON n.hotel_id = h.hotel_id
  AND n.stay_date >= :check_in AND n.stay_date < :check_out
WHERE z.postcode = :postcode
"""


def params(postcode: str = "16803", check_in: str = "2026-10-11",
           check_out: str = "2026-10-13") -> dict[str, str]:
    return {"postcode": postcode, "check_in": check_in, "check_out": check_out}


def retrieve(
    database_path: Path,
    sql: str,
    proposed_params: dict[str, str],
    trusted_params: dict[str, str] | None = None,
) -> RetrievalResult:
    trusted = trusted_params or proposed_params
    request = StayRequest(
        postcode=trusted["postcode"],
        check_in=trusted["check_in"],
        check_out=trusted["check_out"],
    )
    return retrieve_saved_stays(database_path, sql, proposed_params, request)


@pytest.fixture
def fixture_db(tmp_path: Path) -> Path:
    database_path = tmp_path / "rag.sqlite3"
    initialize_database(database_path, DATA_DIRECTORY)
    connection = connect_database(database_path)
    try:
        hotels = (
            ("fixture:campus-lantern", "Campus Lantern", 12000, 2, 11000, 1),
            ("fixture:nittany-budget", "Nittany Budget", 10000, 0, 9000, 3),
            ("fixture:college-green", "College Green", 15000, 1, None, None),
            ("fixture:valley-ridge", "Valley Ridge", 13000, 2, 14000, 2),
        )
        for hotel_id, name, first_rate, first_rooms, second_rate, second_rooms in hotels:
            connection.execute(
                "INSERT INTO saved_hotels VALUES (?, ?, NULL, 40, -77)",
                (hotel_id, name),
            )
            connection.execute(
                "INSERT INTO saved_hotel_zips VALUES (?, '16803', 'us', 40, -77, NULL)",
                (hotel_id,),
            )
            connection.execute(
                "INSERT INTO demo_hotel_nights VALUES (?, '2026-10-11', ?, ?)",
                (hotel_id, first_rate, first_rooms),
            )
            if second_rate is not None:
                connection.execute(
                    "INSERT INTO demo_hotel_nights VALUES (?, '2026-10-12', ?, ?)",
                    (hotel_id, second_rate, second_rooms),
                )
        connection.commit()
    finally:
        connection.close()
    return database_path


def counts(database_path: Path) -> tuple[int, int, int]:
    connection = connect_database(database_path)
    try:
        return tuple(
            connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("saved_hotels", "saved_hotel_zips", "demo_hotel_nights")
        )
    finally:
        connection.close()


def test_checked_one_and_two_night_results(fixture_db: Path) -> None:
    one = retrieve(fixture_db, PROPOSAL, params(check_out="2026-10-12"))
    assert [(stay.name, stay.total_cents) for stay in one.matches] == [
        ("Campus Lantern", 12000), ("Valley Ridge", 13000),
        ("College Green", 15000),
    ]
    assert one.unavailable_ids == ("fixture:nittany-budget",)

    two = retrieve(fixture_db, PROPOSAL, params())
    assert [(stay.name, stay.total_cents) for stay in two.matches] == [
        ("Campus Lantern", 23000), ("Valley Ridge", 27000),
    ]
    assert [[night.stay_date for night in stay.nights] for stay in two.matches] == [
        ["2026-10-11", "2026-10-12"], ["2026-10-11", "2026-10-12"],
    ]
    assert two.incomplete_ids == ("fixture:college-green",)
    assert two.unavailable_ids == ("fixture:nittany-budget",)


def test_no_match_and_missing_nights(fixture_db: Path) -> None:
    assert retrieve(fixture_db, PROPOSAL, params(postcode="16804")).matches == ()
    missing = retrieve(
        fixture_db, PROPOSAL, params(check_in="2026-10-14", check_out="2026-10-15")
    )
    assert missing.matches == ()
    assert len(missing.incomplete_ids) == 4


def test_filtered_candidates_are_distinct_from_saved_zip_count(fixture_db: Path) -> None:
    filtered = retrieve(fixture_db, PROPOSAL + " AND n.nightly_rate_cents <= 5000", params())
    assert filtered.candidate_ids == ()
    assert filtered.matches == ()
    assert filtered.saved_hotel_count == 4
    absent = retrieve(fixture_db, PROPOSAL, params(postcode="16804"))
    assert absent.saved_hotel_count == 0


@pytest.mark.parametrize("proposed_sql", [
    "UPDATE saved_hotels SET name = :postcode WHERE hotel_id = :check_in AND name = :check_out",
    PROPOSAL + "; DELETE FROM saved_hotels",
    "SELECT h.hotel_id FROM saved_hotels h JOIN hotels old ON old.hotel_id=h.hotel_id "
    "WHERE :postcode AND :check_in AND :check_out",
    "SELECT h.hotel_id FROM saved_hotels h WHERE random() AND :postcode "
    "AND :check_in AND :check_out",
    "SELECT h.hotel_id FROM saved_hotels h WHERE 1=:postcode OR 1=:check_in OR 1=:check_out "
    "UNION SELECT name FROM sqlite_master",
])
def test_rejects_writes_multiple_statements_other_tables_and_functions(
    fixture_db: Path, proposed_sql: str
) -> None:
    before = counts(fixture_db)
    with pytest.raises(RetrievalRejectedError):
        retrieve(fixture_db, proposed_sql, params())
    assert counts(fixture_db) == before


def test_rejects_rows_and_bad_parameters(fixture_db: Path) -> None:
    connection = connect_database(fixture_db)
    try:
        for index in range(51):
            hotel_id = f"fixture:extra-{index}"
            connection.execute("INSERT INTO saved_hotels VALUES (?, NULL, NULL, 40, -77)", (hotel_id,))
            connection.execute(
                "INSERT INTO saved_hotel_zips VALUES (?, '16803', 'us', 40, -77, NULL)",
                (hotel_id,),
            )
        connection.commit()
    finally:
        connection.close()
    with pytest.raises(RetrievalRejectedError, match="row limit"):
        retrieve(fixture_db, PROPOSAL, params())
    with pytest.raises(RetrievalRejectedError, match="parameters"):
        retrieve(fixture_db, PROPOSAL, {**params(), "extra": "x"})
    with pytest.raises(RetrievalRejectedError, match="Stay must"):
        retrieve(fixture_db, PROPOSAL, params(check_out="2026-10-11"))

    with pytest.raises(RetrievalRejectedError, match="differ from the requested stay"):
        retrieve(fixture_db, PROPOSAL, params(postcode="16804"), params(postcode="16803"))


def test_execution_budget_interrupts_expensive_proposal(
    fixture_db: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ticks = iter((0.0, 1.0))
    monkeypatch.setattr(retrieval, "monotonic", lambda: next(ticks, 1.0))
    expensive = """
    SELECT h.hotel_id AS hotel_id FROM saved_hotels AS h
    CROSS JOIN saved_hotels AS b CROSS JOIN saved_hotels AS c
    WHERE :postcode AND :check_in AND :check_out
    """
    with pytest.raises(RetrievalRejectedError, match="timed out"):
        retrieve(fixture_db, expensive, params())


def test_version_six_migration_is_additive(fixture_db: Path) -> None:
    before = counts(fixture_db)
    connection = connect_database(fixture_db)
    try:
        for table in ("chat_retrieval_stages", "chat_messages", "chat_conversations"):
            connection.execute(f"DROP TABLE {table}")
        connection.execute("UPDATE app_metadata SET value='6' WHERE key='schema_version'")
        connection.commit()
    finally:
        connection.close()
    assert initialize_database(fixture_db, DATA_DIRECTORY) is False
    assert initialize_database(fixture_db, DATA_DIRECTORY) is False
    connection = connect_database(fixture_db)
    try:
        assert counts(fixture_db) == before
        assert connection.execute(
            "SELECT value FROM app_metadata WHERE key='schema_version'"
        ).fetchone()[0] == "7"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        for table in ("chat_conversations", "chat_messages", "chat_retrieval_stages"):
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
        connection.execute(
            "INSERT INTO chat_conversations VALUES ('fixture:conversation', '2026-10-06T00:00:00Z', '2026-10-06T00:00:00Z')"
        )
        connection.execute(
            "INSERT INTO chat_messages (conversation_id, turn_id, role, content, created_at_utc) "
            "VALUES ('fixture:conversation', 'fixture:turn', 'user', 'Synthetic question', '2026-10-06T00:00:00Z')"
        )
        connection.execute(
            "INSERT INTO chat_retrieval_stages "
            "(conversation_id, turn_id, stage, detail_json, prompt_version, created_at_utc) "
            "VALUES ('fixture:conversation', 'fixture:turn', 'proposal', '{}', '2', '2026-10-06T00:00:00Z')"
        )
        connection.commit()
    finally:
        connection.close()
    reopened = connect_database(fixture_db)
    try:
        assert reopened.execute("SELECT COUNT(*) FROM chat_messages").fetchone()[0] == 1
        assert reopened.execute("SELECT COUNT(*) FROM chat_retrieval_stages").fetchone()[0] == 1
        assert reopened.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        reopened.close()
