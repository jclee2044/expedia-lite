"""Two-call orchestration, history, trace, and safe failure checks."""

import asyncio
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import backend.controllers.rag_chat as rag_chat
from backend.app.main import create_app
from backend.controllers.chat_context import ChatContextError, parse_stay_request
from backend.controllers.database import connect_database
from backend.controllers.gemini import GeminiStreamError, SqlProposal
from backend.models.retrieval import StayRequest

DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"
SQL = """
SELECT DISTINCT h.hotel_id AS hotel_id FROM saved_hotels AS h
JOIN saved_hotel_zips AS z ON z.hotel_id = h.hotel_id
LEFT JOIN demo_hotel_nights AS n ON n.hotel_id = h.hotel_id
  AND n.stay_date >= :check_in AND n.stay_date < :check_out
WHERE z.postcode = :postcode
"""


def _events(response_text: str) -> list[tuple[str, dict[str, str]]]:
    events = []
    for block in response_text.strip().split("\n\n"):
        lines = block.splitlines()
        events.append((lines[0].removeprefix("event: "),
                       json.loads(lines[1].removeprefix("data: "))))
    return events


def _fixture(path: Path) -> None:
    with TestClient(create_app(path, DATA_DIRECTORY)):
        pass
    connection = connect_database(path)
    try:
        for hotel_id, name, first, second, first_rooms in (
            ("fixture:campus", "Campus Lantern", 12000, 11000, 2),
            ("fixture:valley", "Valley Ridge", 13000, 14000, 2),
            ("fixture:budget", "Nittany Budget", 10000, 9000, 0),
        ):
            connection.execute("INSERT INTO saved_hotels VALUES (?, ?, NULL, 40, -77)",
                               (hotel_id, name))
            connection.execute("INSERT INTO saved_hotel_zips VALUES (?, '16803', 'us', 40, -77, NULL)",
                               (hotel_id,))
            connection.execute("INSERT INTO demo_hotel_nights VALUES (?, '2026-10-11', ?, ?)",
                               (hotel_id, first, first_rooms))
            connection.execute("INSERT INTO demo_hotel_nights VALUES (?, '2026-10-12', ?, 2)",
                               (hotel_id, second))
        connection.commit()
    finally:
        connection.close()


def test_parser_requires_unambiguous_dates_and_reuses_explicit_context() -> None:
    first = parse_stay_request("Three cheapest near 16803 on October 11, 2026")
    assert first == StayRequest("16803", "2026-10-11", "2026-10-12")
    assert parse_stay_request("For the same ZIP and dates, which is cheapest?", first) == first
    assert parse_stay_request("Near 16803 from 2026-10-11 to 2026-10-13") == StayRequest(
        "16803", "2026-10-11", "2026-10-13"
    )
    with pytest.raises(ChatContextError, match="dated night"):
        parse_stay_request("Hotels near 16803")
    with pytest.raises(ChatContextError, match="one five-digit ZIP"):
        parse_stay_request("Between 16803 and 16804 on 2026-10-11")


def test_success_followup_and_history_survive_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "rag.sqlite3"
    _fixture(path)
    seen: list[tuple[str, StayRequest, list[dict[str, str]]]] = []

    async def fake_propose(question: str, stay: StayRequest, history: list[dict[str, str]],
                           prompt: str) -> SqlProposal:
        seen.append((question, stay, history))
        return SqlProposal(SQL, {
            "postcode": stay.postcode, "check_in": stay.check_in, "check_out": stay.check_out,
        })

    async def fake_answer(question: str, stay: StayRequest, result, history, prompt):
        assert [item.total_cents for item in result.matches] == [12000, 13000]
        assert result.unavailable_ids == ("fixture:budget",)
        yield '{"hotel_ids":["fixture:campus"],'
        yield '"reason":"lowest_total_cost"}'

    monkeypatch.setattr(rag_chat, "propose_sql", fake_propose)
    monkeypatch.setattr(rag_chat, "stream_grounded_answer", fake_answer)
    question = "Three cheapest near 16803 on October 11, 2026"
    with TestClient(create_app(path, DATA_DIRECTORY)) as client:
        response = client.post("/api/chat/stream", json={"question": question})
        assert response.status_code == 200
        events = _events(response.text)
        assert events[0][0] == "meta" and events[-1][0] == "done"
        answer = "".join(payload["text"] for kind, payload in events if kind == "delta")
        assert "2026-10-11: $120.00/night; 2 simulated rooms." in answer
        conversation_id = events[0][1]["conversation_id"]
        assert client.post("/api/chat/stream", json={"question": "  "}).status_code == 422
        followup = client.post("/api/chat/stream", json={
            "question": "For the same ZIP and dates, which is cheapest?",
            "conversation_id": conversation_id,
        })
        assert _events(followup.text)[-1][0] == "done"
    assert seen[1][1] == StayRequest("16803", "2026-10-11", "2026-10-12")
    assert seen[1][2][-1]["role"] == "assistant"

    with TestClient(create_app(path, DATA_DIRECTORY)) as restarted:
        history = restarted.get("/api/chat/history", params={"conversation_id": conversation_id})
        assert history.status_code == 200
        assert [message["role"] for message in history.json()["messages"]] == [
            "user", "assistant", "user", "assistant"
        ]
        assert history.json()["last_error"] is None
        assert history.json()["last_error_code"] is None
    connection = connect_database(path)
    try:
        stages = connection.execute(
            "SELECT stage, detail_json, prompt_version FROM chat_retrieval_stages "
            "WHERE conversation_id = ? ORDER BY stage_id", (conversation_id,),
        ).fetchall()
        assert [row["stage"] for row in stages] == [
            "proposal", "execution", "result", "proposal", "execution", "result"
        ]
        assert all(row["prompt_version"] == "6" for row in stages)
        result = json.loads(stages[2]["detail_json"])
        assert result["retrieval"]["matches"][0]["total_cents"] == 12000
        assert result["second_model_answer"]["hotel_ids"] == ["fixture:campus"]
        assert result["answer_validation"].startswith("passed")
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        connection.close()


def test_no_match_and_rejected_sql_are_traced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "rag.sqlite3"
    _fixture(path)

    async def fake_propose(question: str, stay: StayRequest, history, prompt):
        sql = "DELETE FROM saved_hotels WHERE hotel_id=:postcode" if "invalid" in question else SQL
        return SqlProposal(sql, {
            "postcode": stay.postcode, "check_in": stay.check_in, "check_out": stay.check_out,
        })

    async def fake_answer(question, stay, result, history, prompt):
        assert result.matches == ()
        yield '{"hotel_ids":[],"reason":"no_match"}'

    monkeypatch.setattr(rag_chat, "propose_sql", fake_propose)
    monkeypatch.setattr(rag_chat, "stream_grounded_answer", fake_answer)
    with TestClient(create_app(path, DATA_DIRECTORY)) as client:
        no_match = _events(client.post("/api/chat/stream", json={
            "question": "Hotels near 16804 on 2026-10-11?"
        }).text)
        assert no_match[-1][0] == "done"
        rejected = _events(client.post("/api/chat/stream", json={
            "question": "invalid query near 16803 on 2026-10-11"
        }).text)
        assert rejected[-1][0] == "error"
        assert "rejected" in rejected[-1][1]["message"]
        rejected_id = rejected[0][1]["conversation_id"]
        history = client.get("/api/chat/history", params={"conversation_id": rejected_id}).json()
        assert [message["role"] for message in history["messages"]] == ["user"]
        assert "rejected" in history["last_error"]
        assert history["last_error_code"] == "retryable"
    connection = connect_database(path)
    try:
        assert connection.execute("SELECT COUNT(*) FROM saved_hotels").fetchone()[0] == 3
        assert [row[0] for row in connection.execute(
            "SELECT stage FROM chat_retrieval_stages WHERE conversation_id = ? ORDER BY stage_id",
            (rejected_id,),
        )] == ["proposal", "execution", "error"]
    finally:
        connection.close()


def test_partial_second_call_failure_keeps_error_without_assistant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "rag.sqlite3"
    _fixture(path)

    async def fake_propose(question: str, stay: StayRequest, history, prompt):
        return SqlProposal(SQL, {
            "postcode": stay.postcode, "check_in": stay.check_in, "check_out": stay.check_out,
        })

    async def fake_answer(question, stay, result, history, prompt):
        yield "Partial answer"
        raise GeminiStreamError("Gemini timed out. Try again.")

    monkeypatch.setattr(rag_chat, "propose_sql", fake_propose)
    monkeypatch.setattr(rag_chat, "stream_grounded_answer", fake_answer)
    with TestClient(create_app(path, DATA_DIRECTORY)) as client:
        events = _events(client.post("/api/chat/stream", json={
            "question": "Hotels near 16803 on 2026-10-11"
        }).text)
        assert [kind for kind, _ in events] == ["meta", "error"]
        conversation_id = events[0][1]["conversation_id"]
        history = client.get("/api/chat/history", params={"conversation_id": conversation_id}).json()
        assert [message["role"] for message in history["messages"]] == ["user"]
        assert history["last_error"] == "Gemini timed out. Try again."
        assert history["last_error_code"] == "retryable"


def test_missing_context_is_saved_as_editable_error(tmp_path: Path) -> None:
    path = tmp_path / "rag.sqlite3"
    _fixture(path)
    with TestClient(create_app(path, DATA_DIRECTORY)) as client:
        events = _events(client.post("/api/chat/stream", json={
            "question": "Which saved hotels are available?"
        }).text)
        assert [kind for kind, _ in events] == ["meta", "error"]
        assert events[-1][1]["code"] == "missing_context"
        history = client.get("/api/chat/history", params={
            "conversation_id": events[0][1]["conversation_id"]
        }).json()
        assert history["last_error_code"] == "missing_context"
        assert [message["role"] for message in history["messages"]] == ["user"]


def test_hallucinated_fact_never_reaches_browser_or_successful_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "rag.sqlite3"
    _fixture(path)

    async def fake_propose(question, stay, history, prompt):
        return SqlProposal(SQL, {
            "postcode": stay.postcode, "check_in": stay.check_in, "check_out": stay.check_out,
        })

    async def fake_answer(question, stay, result, history, prompt):
        yield '{"hotel_ids":["fixture:valley"],"reason":"available_for_stay",'
        yield '"answer":"October 14 costs $140"}'

    monkeypatch.setattr(rag_chat, "propose_sql", fake_propose)
    monkeypatch.setattr(rag_chat, "stream_grounded_answer", fake_answer)
    with TestClient(create_app(path, DATA_DIRECTORY)) as client:
        events = _events(client.post("/api/chat/stream", json={
            "question": "Compare 16803 from 2026-10-11 to 2026-10-13"
        }).text)
        assert [kind for kind, _ in events] == ["meta", "error"]
        history = client.get("/api/chat/history", params={
            "conversation_id": events[0][1]["conversation_id"]
        }).json()
        assert [message["role"] for message in history["messages"]] == ["user"]
        assert "could not be checked" in history["last_error"]


def test_closed_stream_records_interruption_without_assistant(tmp_path: Path) -> None:
    path = tmp_path / "rag.sqlite3"
    _fixture(path)

    async def close_after_metadata() -> str:
        stream = rag_chat.stream_rag_answer(
            path, "Hotels near 16803 on 2026-10-11", None, "Prompt"
        )
        first = await anext(stream)
        await stream.aclose()
        return first.payload["conversation_id"]

    conversation_id = asyncio.run(close_after_metadata())
    with TestClient(create_app(path, DATA_DIRECTORY)) as client:
        history = client.get("/api/chat/history", params={
            "conversation_id": conversation_id
        }).json()
        assert [message["role"] for message in history["messages"]] == ["user"]
        assert history["last_error"] == "The chat request was interrupted."
