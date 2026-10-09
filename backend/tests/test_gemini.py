"""Mocked raw Gemini streaming and chat route checks; no live API calls."""

import asyncio
import json

import httpx
import pytest
import backend.controllers.gemini as gemini
from backend.models.retrieval import RetrievalResult, StayRequest, VerifiedNight, VerifiedStay


def _provider_event(text: str, finish: str | None = None) -> str:
    candidate = {"content": {"parts": [{"text": text}]}}
    if finish is not None:
        candidate["finishReason"] = finish
    return f'data: {json.dumps({"candidates": [candidate]})}\n\n'


def test_raw_gemini_stream_uses_prompt_context_and_yields_chunks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, text=_provider_event("Hello ") + _provider_event("there."))

    monkeypatch.setattr(gemini, "get_gemini_api_key", lambda: "synthetic-key")
    async def collect() -> list[str]:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            return [chunk async for chunk in gemini.stream_raw_answer(
                "What can you do?", [{"role": "user", "content": "Hi"}], client=client,
            )]

    chunks = asyncio.run(collect())

    assert chunks == ["Hello ", "there."]
    assert len(requests) == 1
    assert requests[0].headers["x-goog-api-key"] == "synthetic-key"
    assert requests[0].url.params["alt"] == "sse"
    sent = json.loads(requests[0].content)
    assert sent["contents"] == [
        {"role": "user", "parts": [{"text": "Hi"}]},
        {"role": "user", "parts": [{"text": "What can you do?"}]},
    ]
    assert "Current mode: preview_chat" in sent["systemInstruction"]["parts"][0]["text"]
    assert "saved_hotels" not in sent["contents"]


@pytest.mark.parametrize(
    ("status", "expected"),
    [(429, "rate limit"), (403, "access"), (500, "could not complete")],
)
def test_provider_http_failures_are_sanitized(
    monkeypatch: pytest.MonkeyPatch, status: int, expected: str,
) -> None:
    monkeypatch.setattr(gemini, "get_gemini_api_key", lambda: "synthetic-key")
    async def collect() -> list[str]:
        async with httpx.AsyncClient(transport=httpx.MockTransport(
            lambda _: httpx.Response(status, text="private provider detail synthetic-key")
        )) as client:
            return [part async for part in gemini.stream_raw_answer("Hello", [], client=client)]

    with pytest.raises(gemini.GeminiStreamError, match=expected) as captured:
        asyncio.run(collect())
    assert "synthetic-key" not in str(captured.value)
    assert "private provider detail" not in str(captured.value)


def test_sql_proposal_uses_json_mode_and_grounded_call_receives_checked_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[httpx.Request] = []
    sql = "SELECT h.hotel_id AS hotel_id FROM saved_hotels AS h WHERE :postcode AND :check_in AND :check_out"
    proposal = {"sql": sql, "params": {
        "postcode": "16803", "check_in": "2026-10-11", "check_out": "2026-10-12",
    }}

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if "streamGenerateContent" in str(request.url):
            return httpx.Response(200, text=_provider_event(
                '{"hotel_ids":["fixture:campus-lantern"],"reason":"lowest_total_cost"}', "STOP"
            ))
        return httpx.Response(200, json={"candidates": [{"content": {
            "parts": [{"text": json.dumps(proposal)}]
        }}]})

    monkeypatch.setattr(gemini, "get_gemini_api_key", lambda: "synthetic-key")
    stay = StayRequest("16803", "2026-10-11", "2026-10-12")
    result = RetrievalResult(
        ("fixture:campus-lantern",),
        (VerifiedStay("fixture:campus-lantern", "Campus Lantern", None, "16803",
                      (VerifiedNight("2026-10-11", 12000, 2),), 12000),), (), (), 1,
    )

    async def collect():
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            generated = await gemini.propose_sql("Cheapest?", stay, [], "Prompt", client=client)
            chunks = [chunk async for chunk in gemini.stream_grounded_answer(
                "Cheapest?", stay, result, [], "Prompt", client=client,
            )]
            return generated, chunks

    generated, chunks = asyncio.run(collect())
    assert generated.sql == sql
    assert json.loads("".join(chunks))["hotel_ids"] == ["fixture:campus-lantern"]
    assert len(calls) == 2
    assert all(call.headers["x-goog-api-key"] == "synthetic-key" for call in calls)
    first = json.loads(calls[0].content)
    second = json.loads(calls[1].content)
    assert first["generationConfig"]["responseMimeType"] == "application/json"
    assert "Current mode: sql_proposal" in first["systemInstruction"]["parts"][0]["text"]
    assert "Current mode: grounded_answer" in second["systemInstruction"]["parts"][0]["text"]
    assert '"nightly_rate_cents": 12000' in second["contents"][-1]["parts"][0]["text"]
    assert '"saved_hotel_count": 1' in second["contents"][-1]["parts"][0]["text"]
    assert second["generationConfig"]["responseJsonSchema"]["additionalProperties"] is False


@pytest.mark.parametrize("finish", [None, "MAX_TOKENS", "SAFETY"])
def test_grounded_stream_requires_a_complete_provider_answer(
    monkeypatch: pytest.MonkeyPatch, finish: str | None,
) -> None:
    monkeypatch.setattr(gemini, "get_gemini_api_key", lambda: "synthetic-key")

    async def collect() -> list[str]:
        async with httpx.AsyncClient(transport=httpx.MockTransport(
            lambda _: httpx.Response(200, text=_provider_event(
                '{"hotel_ids":[],"reason":"no_match"}', finish
            ))
        )) as client:
            return [part async for part in gemini.stream_grounded_answer(
                "Question", StayRequest("16803", "2026-10-11", "2026-10-12"),
                RetrievalResult((), (), (), (), 3), [], "Prompt", client=client,
            )]

    with pytest.raises(gemini.GeminiStreamError, match="did not finish"):
        asyncio.run(collect())


def test_malformed_sql_proposal_fails_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gemini, "get_gemini_api_key", lambda: "synthetic-key")
    async def collect():
        async with httpx.AsyncClient(transport=httpx.MockTransport(
            lambda _: httpx.Response(200, json={"candidates": [{"content": {
                "parts": [{"text": "not-json"}]
            }}]})
        )) as client:
            return await gemini.propose_sql(
                "Question", StayRequest("16803", "2026-10-11", "2026-10-12"),
                [], "Prompt", client=client,
            )
    with pytest.raises(gemini.GeminiStreamError, match="invalid SQL proposal"):
        asyncio.run(collect())
