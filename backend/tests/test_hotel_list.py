"""ZIP-only hotel identity retrieval and clarification regression checks."""

import asyncio
import json
from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.controllers import gemini, rag_chat
from backend.controllers.chat_context import ChatContextError, parse_hotel_request
from backend.controllers.database import connect_database, initialize_database
from backend.controllers.grounded_answer import GroundingError, render_grounded_answer
from backend.controllers.retrieval import RetrievalRejectedError, retrieve_saved_hotels
from backend.inspect_rag_demo import inspect_turn
from backend.models.retrieval import HotelListRequest, HotelListResult, StayRequest

DATA = Path(__file__).resolve().parents[2] / "data"
SQL = ("SELECT h.hotel_id AS hotel_id FROM saved_hotels h "
       "JOIN saved_hotel_zips z ON z.hotel_id=h.hotel_id WHERE z.postcode=:postcode")


@pytest.fixture
def database(tmp_path: Path) -> Path:
    path = tmp_path / "hotel-list.sqlite3"
    initialize_database(path, DATA)
    connection = connect_database(path)
    try:
        for hotel_id, name, postcode in [
            ("campus", "Campus", "16803"), ("zero", "Zero Rooms", "16803"),
            ("missing", "Missing Nights", "16803"), ("away", "Other ZIP", "17042"),
        ]:
            connection.execute("INSERT INTO saved_hotels VALUES (?, ?, NULL, 40, -77)", (hotel_id, name))
            connection.execute("INSERT INTO saved_hotel_zips VALUES (?, ?, 'us', 40, -77, NULL)",
                               (hotel_id, postcode))
        connection.execute("INSERT INTO demo_hotel_nights VALUES ('zero', '2026-10-11', 10000, 0)")
        connection.commit()
    finally:
        connection.close()
    return path


def test_identity_questions_do_not_require_dates_but_prices_and_rooms_do() -> None:
    assert parse_hotel_request("17042 has what hotels") == HotelListRequest("17042")
    assert parse_hotel_request("Which saved hotels near ZIP 00501?") == HotelListRequest("00501")
    for question in ["What hotels near 16803 are available?", "Hotels in 16803 under $50?",
                     "Cheapest hotels near 16803", "Hotels for October 11 near 16803"]:
        with pytest.raises(ChatContextError, match="dated night"):
            parse_hotel_request(question)
    with pytest.raises(ChatContextError, match="five-digit ZIP"):
        parse_hotel_request("Which saved hotels?")
    with pytest.raises(ChatContextError, match="one five-digit ZIP"):
        parse_hotel_request("Hotels in 16803 and 17042")
    previous = HotelListRequest("16803")
    assert parse_hotel_request("Show hotels there", previous) == previous
    assert parse_hotel_request("Hotels there on 2026-10-11", previous) == StayRequest(
        "16803", "2026-10-11", "2026-10-12")
    with pytest.raises(ChatContextError, match="dated night"):
        parse_hotel_request("Available hotels there", previous)


def test_identity_rows_include_hotels_without_available_nightly_data(database: Path) -> None:
    request = HotelListRequest("16803")
    result = retrieve_saved_hotels(database, SQL, {"postcode": "16803"}, request)
    assert {hotel.hotel_id for hotel in result.hotels} == {"campus", "zero", "missing"}
    assert result.saved_hotel_count == 3
    # Even a broad model query cannot add a hotel associated with another ZIP.
    broad = "SELECT h.hotel_id AS hotel_id FROM saved_hotels h WHERE :postcode=:postcode"
    assert {hotel.hotel_id for hotel in retrieve_saved_hotels(
        database, broad, {"postcode": "16803"}, request).hotels} == {"campus", "zero", "missing"}
    absent = retrieve_saved_hotels(database, SQL, {"postcode": "16804"}, HotelListRequest("16804"))
    assert absent.hotels == () and absent.saved_hotel_count == 0


@pytest.mark.parametrize("sql", [
    "UPDATE saved_hotels SET name=:postcode",
    SQL + "; DELETE FROM saved_hotels",
    "SELECT h.hotel_id FROM hotels h WHERE :postcode",
    "SELECT h.hotel_id FROM saved_hotels h WHERE :postcode AND random()",
])
def test_zip_only_queries_keep_read_only_restrictions(database: Path, sql: str) -> None:
    connection = connect_database(database)
    before = [tuple(row) for row in connection.execute("SELECT * FROM saved_hotels ORDER BY hotel_id")]
    connection.close()
    with pytest.raises(RetrievalRejectedError):
        retrieve_saved_hotels(database, sql, {"postcode": "16803"}, HotelListRequest("16803"))
    connection = connect_database(database)
    assert [tuple(row) for row in connection.execute("SELECT * FROM saved_hotels ORDER BY hotel_id")] == before
    connection.close()


def test_zip_only_bind_values_cannot_override_the_question(database: Path) -> None:
    with pytest.raises(RetrievalRejectedError):
        retrieve_saved_hotels(database, SQL, {"postcode": "17042"}, HotelListRequest("16803"))
    with pytest.raises(RetrievalRejectedError):
        retrieve_saved_hotels(database, SQL, {"postcode": "16803", "check_in": "2026-10-11"},
                              HotelListRequest("16803"))


def test_identity_answers_never_claim_dates_prices_or_available_rooms(database: Path) -> None:
    request = HotelListRequest("16803")
    result = retrieve_saved_hotels(database, SQL, {"postcode": "16803"}, request)
    raw = json.dumps({"hotel_ids": [hotel.hotel_id for hotel in result.hotels], "reason": "saved_hotels"})
    answer, _ = render_grounded_answer(raw, request, result)
    assert all(name in answer for name in ["Campus", "Zero Rooms", "Missing Nights"])
    assert "$" not in answer and "2026-" not in answer
    assert "not a complete area inventory" in answer
    for proposal in [
        {"hotel_ids": ["away"], "reason": "saved_hotels"},
        {"hotel_ids": ["campus"], "reason": "available_for_stay"},
        {"hotel_ids": ["campus"], "reason": "saved_hotels", "answer": "Available for $50"},
    ]:
        with pytest.raises(GroundingError):
            render_grounded_answer(json.dumps(proposal), request, result)
    empty, _ = render_grounded_answer('{"hotel_ids":[],"reason":"no_match"}', request,
                                     HotelListResult((), (), 3))
    assert "No hotel is saved" not in empty


def test_gemini_identity_calls_send_zip_only_and_checked_metadata(
    database: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[httpx.Request] = []
    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        answer = {"hotel_ids": ["campus"], "reason": "saved_hotels"}
        if "streamGenerateContent" in str(request.url):
            candidate = {"content": {"parts": [{"text": json.dumps(answer)}]}, "finishReason": "STOP"}
            return httpx.Response(200, text="data: " + json.dumps({"candidates": [candidate]}) + "\n\n")
        proposal = {"sql": SQL, "params": {"postcode": "16803"}}
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": json.dumps(proposal)}]}}]})
    monkeypatch.setattr(gemini, "get_gemini_api_key", lambda: "synthetic-key")
    request = HotelListRequest("16803")
    result = retrieve_saved_hotels(database, SQL, {"postcode": "16803"}, request)
    async def collect() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            proposal = await gemini.propose_sql("Which saved hotels in 16803?", request, [], "Prompt", client=client)
            assert proposal.params == {"postcode": "16803"}
            chunks = [chunk async for chunk in gemini.stream_grounded_answer(
                "Which saved hotels in 16803?", request, result, [], "Prompt", client=client)]
            assert json.loads("".join(chunks))["reason"] == "saved_hotels"
    asyncio.run(collect())
    first, second = [json.loads(call.content) for call in calls]
    assert "hotel_list" in first["systemInstruction"]["parts"][0]["text"]
    facts = json.loads(second["contents"][-1]["parts"][0]["text"].split("Checked backend retrieval JSON: ")[1])
    assert facts["request"] == {"postcode": "16803"} and facts["request_kind"] == "hotel_list"
    assert all("nights" not in hotel and "total_cents" not in hotel for hotel in facts["matches"])
    assert second["generationConfig"]["responseJsonSchema"]["properties"]["reason"]["enum"] == [
        "saved_hotels", "no_match"]


def test_identity_two_call_trace_restores_and_inspects_without_dates(
    database: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    calls: list[str] = []
    async def proposal(question: str, request: HotelListRequest, history: list, prompt: str) -> gemini.SqlProposal:
        calls.append("proposal")
        assert isinstance(request, HotelListRequest)
        return gemini.SqlProposal(SQL, {"postcode": request.postcode})
    async def answer(question: str, request: HotelListRequest, result: HotelListResult,
                     history: list, prompt: str) -> AsyncIterator[str]:
        calls.append("second request")
        yield json.dumps({"hotel_ids": [hotel.hotel_id for hotel in result.hotels], "reason": "saved_hotels"})
    monkeypatch.setattr(rag_chat, "propose_sql", proposal)
    monkeypatch.setattr(rag_chat, "stream_grounded_answer", answer)
    with TestClient(create_app(database, DATA)) as client:
        response = client.post("/api/chat/stream", json={"question": "16803 has what hotels"})
        blocks = response.text.strip().split("\n\n")
        meta = json.loads(blocks[0].split("data: ")[1])
        assert "event: done" in response.text and "Zero Rooms" in response.text
        conversation_id = meta["conversation_id"]
    assert calls == ["proposal", "second request"]
    inspect_turn(database, meta["turn_id"])
    assert "DIRECT SQLITE ROWS" in capsys.readouterr().out
    with TestClient(create_app(database, DATA)) as client:
        history = client.get("/api/chat/history", params={"conversation_id": conversation_id}).json()
        assert history["messages"][-1]["role"] == "assistant"
        followup = client.post("/api/chat/stream", json={
            "question": "Show hotels there", "conversation_id": conversation_id})
        assert "event: done" in followup.text
        before = len(calls)
        missing = client.post("/api/chat/stream", json={
            "question": "Which hotels there are available?", "conversation_id": conversation_id})
        assert '"code": "missing_context"' in missing.text and "event: done" not in missing.text
        assert len(calls) == before  # A clarification makes no provider requests.
        restored = client.get("/api/chat/history", params={"conversation_id": conversation_id}).json()
        assert restored["last_error_code"] == "missing_context"
