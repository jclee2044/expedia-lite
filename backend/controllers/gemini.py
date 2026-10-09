"""Framework-free Gemini SQL proposal and grounded answer calls."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal, TypedDict

import httpx

from backend.config import PROJECT_ROOT, get_gemini_api_key
from backend.controllers.grounded_answer import HOTEL_LIST_REASONS, MAX_GROUNDED_HOTELS, RECOMMENDATION_REASONS
from backend.models.retrieval import HotelListRequest, HotelListResult, RetrievalResult, StayRequest

MODEL = "gemini-3.5-flash-lite"
STREAM_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:streamGenerateContent"
GENERATE_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
PROMPT_PATH = PROJECT_ROOT / "prompts" / "hotel-assistant.md"
MAX_HISTORY_MESSAGES = 6
MAX_HISTORY_CHARS = 1000


class ChatTurn(TypedDict):
    role: Literal["user", "assistant"]
    content: str


class GeminiStreamError(Exception):
    """Safe message to return to the chat client."""


@dataclass(frozen=True)
class SqlProposal:
    sql: str
    params: dict[str, str]


def load_assistant_prompt() -> str:
    """Read the versioned project prompt, including the actual SQLite schema."""
    try:
        return Path(PROMPT_PATH).read_text(encoding="utf-8")
    except OSError:
        raise GeminiStreamError("The hotel assistant prompt is unavailable.") from None


def _api_key() -> str:
    key = get_gemini_api_key()
    if key is None:
        raise GeminiStreamError("Gemini is not configured on the backend.")
    return key


def _check_status(status_code: int) -> None:
    if status_code == 429:
        raise GeminiStreamError("Gemini is busy or at its rate limit. Try again later.")
    if status_code in (401, 403):
        raise GeminiStreamError("Gemini access is unavailable for this project.")
    if status_code >= 400:
        raise GeminiStreamError("Gemini could not complete this reply.")


def build_contents(question: str, history: list[ChatTurn]) -> list[dict[str, object]]:
    """Convert a bounded recent conversation into Gemini's content shape."""
    recent = history[-MAX_HISTORY_MESSAGES:]
    contents: list[dict[str, object]] = [
        {"role": "model" if turn["role"] == "assistant" else "user",
         "parts": [{"text": turn["content"][:MAX_HISTORY_CHARS]}]}
        for turn in recent
    ]
    contents.append({"role": "user", "parts": [{"text": question}]})
    return contents


async def stream_raw_answer(
    question: str,
    history: list[ChatTurn],
    *,
    client: httpx.AsyncClient | None = None,
) -> AsyncIterator[str]:
    """Yield model text only; never send the key or raw provider errors onward."""
    key = _api_key()
    prompt = load_assistant_prompt()

    payload = {
        "systemInstruction": {"parts": [{"text": prompt + "\n\nCurrent mode: preview_chat."}]},
        "contents": build_contents(question, history),
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 512},
    }
    owns_client = client is None
    if client is None:
        client = httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0))
    saw_text = False
    try:
        async with client.stream(
            "POST", STREAM_URL, params={"alt": "sse"},
            headers={"x-goog-api-key": key}, json=payload,
        ) as response:
            _check_status(response.status_code)
            data_lines: list[str] = []
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    data_lines.append(line[5:].strip())
                elif not line and data_lines:
                    for text in _extract_text("\n".join(data_lines)):
                        saw_text = True
                        yield text
                    data_lines.clear()
            if data_lines:
                for text in _extract_text("\n".join(data_lines)):
                    saw_text = True
                    yield text
    except httpx.TimeoutException:
        raise GeminiStreamError("Gemini timed out. Try again.") from None
    except httpx.RequestError:
        raise GeminiStreamError("Gemini is unavailable. Try again.") from None
    finally:
        if owns_client:
            await client.aclose()
    if not saw_text:
        raise GeminiStreamError("Gemini returned no answer. Try again.")


def _extract_text(data: str) -> list[str]:
    try:
        chunk = json.loads(data)
        candidates = chunk.get("candidates", [])
        parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
        return [part["text"] for part in parts
                if isinstance(part, dict) and isinstance(part.get("text"), str)
                and not part.get("thought")]
    except (ValueError, AttributeError, IndexError, TypeError):
        raise GeminiStreamError("Gemini sent an invalid stream. Try again.") from None


async def propose_sql(
    question: str, request: StayRequest | HotelListRequest, history: list[ChatTurn], prompt: str,
    *, client: httpx.AsyncClient | None = None,
) -> SqlProposal:
    """Ask Gemini for one JSON SQL proposal; no database handle is supplied."""
    key = _api_key()
    template = (
        "SELECT DISTINCT h.hotel_id AS hotel_id FROM saved_hotels AS h "
        "JOIN saved_hotel_zips AS z ON z.hotel_id = h.hotel_id "
        "LEFT JOIN demo_hotel_nights AS n ON n.hotel_id = h.hotel_id "
        "AND n.stay_date >= :check_in AND n.stay_date < :check_out "
        "WHERE z.postcode = :postcode"
    )
    listing = isinstance(request, HotelListRequest)
    if listing:
        template = (
            "SELECT DISTINCT h.hotel_id AS hotel_id FROM saved_hotels AS h "
            "JOIN saved_hotel_zips AS z ON z.hotel_id = h.hotel_id "
            "WHERE z.postcode = :postcode"
        )
    bind_rules = (
        "postcode only; this is a hotel_list lookup with no dates, prices or availability. "
        if listing else "postcode, check_in, check_out "
    )
    instruction = (
        prompt + "\n\nCurrent mode: sql_proposal. Return only JSON with exactly "
        "sql and params keys. params must have " + bind_rules +
        "matching the backend values. The SQL must return one hotel_id column. "
        "Prefer this safe candidate query unless a narrower query is needed: " + template
    )
    ask = question + "\n\nBackend-verified request: " + json.dumps(asdict(request))
    payload = {
        "systemInstruction": {"parts": [{"text": instruction}]},
        "contents": build_contents(ask, history),
        "generationConfig": {
            "temperature": 0, "maxOutputTokens": 1024,
            "responseMimeType": "application/json",
        },
    }
    owns_client = client is None
    if client is None:
        client = httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0))
    try:
        response = await client.post(
            GENERATE_URL, headers={"x-goog-api-key": key}, json=payload
        )
        _check_status(response.status_code)
        body = response.json()
        parts = body["candidates"][0]["content"]["parts"]
        raw = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
        proposal = json.loads(raw)
        if not isinstance(proposal, dict) or set(proposal) != {"sql", "params"}:
            raise ValueError
        if not isinstance(proposal["sql"], str) or not isinstance(proposal["params"], dict):
            raise ValueError
        if any(not isinstance(key, str) or not isinstance(value, str)
               for key, value in proposal["params"].items()):
            raise ValueError
        return SqlProposal(proposal["sql"], proposal["params"])
    except httpx.TimeoutException:
        raise GeminiStreamError("Gemini timed out. Try again.") from None
    except httpx.RequestError:
        raise GeminiStreamError("Gemini is unavailable. Try again.") from None
    except (ValueError, KeyError, IndexError, TypeError):
        raise GeminiStreamError("Gemini returned an invalid SQL proposal.") from None
    finally:
        if owns_client:
            await client.aclose()


async def stream_grounded_answer(
    question: str, request: StayRequest | HotelListRequest, result: RetrievalResult | HotelListResult,
    history: list[ChatTurn], prompt: str,
    *, client: httpx.AsyncClient | None = None,
) -> AsyncIterator[str]:
    """Stream text from a second Gemini request containing only checked facts."""
    key = _api_key()
    facts = {
        "request": asdict(request),
        "matches": [asdict(stay) for stay in result.matches[:MAX_GROUNDED_HOTELS]],
        "candidate_count": len(result.candidate_ids),
        "saved_hotel_count": result.saved_hotel_count,
        "incomplete_count": len(result.incomplete_ids),
        "unavailable_count": len(result.unavailable_ids),
        "truncated": len(result.matches) > MAX_GROUNDED_HOTELS,
    } if isinstance(result, RetrievalResult) else {
        "request_kind": "hotel_list", "request": asdict(request),
        "matches": [asdict(hotel) for hotel in result.hotels[:MAX_GROUNDED_HOTELS]],
        "candidate_count": len(result.candidate_ids),
        "saved_hotel_count": result.saved_hotel_count,
        "truncated": len(result.hotels) > MAX_GROUNDED_HOTELS,
    }
    reasons = HOTEL_LIST_REASONS if isinstance(result, HotelListResult) else RECOMMENDATION_REASONS
    ask = question + "\n\nChecked backend retrieval JSON: " + json.dumps(facts)
    payload = {
        "systemInstruction": {"parts": [{"text": prompt + "\n\nCurrent mode: grounded_answer. "
                                  "Use only the checked JSON from this request for hotel facts."}]},
        "contents": build_contents(ask, history),
        "generationConfig": {
            "temperature": 0, "maxOutputTokens": 768,
            "responseMimeType": "application/json",
            "responseJsonSchema": {
                "type": "object",
                "properties": {
                    "hotel_ids": {"type": "array", "items": {"type": "string"},
                                  "maxItems": MAX_GROUNDED_HOTELS},
                    "reason": {"type": "string", "enum": list(reasons)},
                },
                "required": ["hotel_ids", "reason"], "additionalProperties": False,
            },
        },
    }
    owns_client = client is None
    if client is None:
        client = httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0))
    saw_text = False
    finished = False

    def checked_parts(data: str) -> list[str]:
        nonlocal finished
        parts = _extract_text(data)
        candidate = (json.loads(data).get("candidates") or [{}])[0]
        finish = candidate.get("finishReason")
        if finish is not None:
            if finish != "STOP":
                raise GeminiStreamError("Gemini did not finish a checked answer. Try again.")
            finished = True
        return parts

    try:
        async with client.stream(
            "POST", STREAM_URL, params={"alt": "sse"},
            headers={"x-goog-api-key": key}, json=payload,
        ) as response:
            _check_status(response.status_code)
            data_lines: list[str] = []
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    data_lines.append(line[5:].strip())
                elif not line and data_lines:
                    for chunk in checked_parts("\n".join(data_lines)):
                        saw_text = True
                        yield chunk
                    data_lines.clear()
            if data_lines:
                for chunk in checked_parts("\n".join(data_lines)):
                    saw_text = True
                    yield chunk
    except httpx.TimeoutException:
        raise GeminiStreamError("Gemini timed out. Try again.") from None
    except httpx.RequestError:
        raise GeminiStreamError("Gemini is unavailable. Try again.") from None
    finally:
        if owns_client:
            await client.aclose()
    if not saw_text:
        raise GeminiStreamError("Gemini returned no answer. Try again.")
    if not finished:
        raise GeminiStreamError("Gemini did not finish a checked answer. Try again.")
