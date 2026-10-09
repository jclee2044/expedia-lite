"""Orchestrate two Gemini calls around checked, read-only hotel retrieval."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import asdict, dataclass
from pathlib import Path

from backend.controllers.chat_context import ChatContextError, parse_hotel_request
from backend.controllers.chat_history import save_assistant, save_stage, start_turn
from backend.controllers.gemini import GeminiStreamError, propose_sql, stream_grounded_answer
from backend.controllers.grounded_answer import GroundingError, render_grounded_answer
from backend.controllers.retrieval import RetrievalRejectedError, retrieve_saved_hotels, retrieve_saved_stays
from backend.models.retrieval import HotelListRequest

MAX_ANSWER_CHARS = 6000


@dataclass(frozen=True)
class ChatEvent:
    kind: str
    payload: dict[str, str]


async def stream_rag_answer(
    database_path: Path, question: str, conversation_id: str | None, prompt: str
) -> AsyncIterator[ChatEvent]:
    """Persist each stage; never save an incomplete model answer as success."""
    started = start_turn(database_path, conversation_id, question)
    history = [
        {"role": message.role, "content": message.content}
        for message in started.previous_messages[-6:]
    ]
    error_saved = False
    completed = False
    try:
        yield ChatEvent("meta", {
            "conversation_id": started.conversation_id,
            "turn_id": started.turn_id,
        })
        stay = parse_hotel_request(question, started.previous_request)
        proposal = await propose_sql(question, stay, history, prompt)
        save_stage(database_path, started.conversation_id, started.turn_id,
                   "proposal", {"sql": proposal.sql, "params": proposal.params})
        save_stage(database_path, started.conversation_id, started.turn_id,
                   "execution", {"sql": proposal.sql, "params": proposal.params,
                                 "status": "attempted"})
        retrieve = retrieve_saved_hotels if isinstance(stay, HotelListRequest) else retrieve_saved_stays
        result = retrieve(database_path, proposal.sql, proposal.params, stay)
        save_stage(database_path, started.conversation_id, started.turn_id,
                   "result", {"request": asdict(stay), "retrieval": asdict(result)})
        chunks: list[str] = []
        length = 0
        async for chunk in stream_grounded_answer(question, stay, result, history, prompt):
            length += len(chunk)
            if length > MAX_ANSWER_CHARS:
                raise GeminiStreamError("Gemini replied with too much text. Try again.")
            chunks.append(chunk)
        answer, recommendation = render_grounded_answer("".join(chunks), stay, result)
        if len(answer) > MAX_ANSWER_CHARS:
            raise GeminiStreamError("The checked answer is too long. Ask for fewer hotels.")
        save_assistant(database_path, started.conversation_id, started.turn_id, answer, recommendation)
        completed = True
        for offset in range(0, len(answer), 240):
            yield ChatEvent("delta", {"text": answer[offset:offset + 240]})
        yield ChatEvent("done", {})
    except asyncio.CancelledError:
        save_stage(database_path, started.conversation_id, started.turn_id,
                   "error", {"message": "The chat request was interrupted."})
        error_saved = True
        raise
    except (ChatContextError, GeminiStreamError, RetrievalRejectedError, GroundingError) as error:
        code = "missing_context" if isinstance(error, ChatContextError) else "retryable"
        message = (
            "The generated hotel query was rejected. Try again."
            if isinstance(error, RetrievalRejectedError) else str(error)
        )
        save_stage(database_path, started.conversation_id, started.turn_id,
                   "error", {"message": message, "code": code})
        error_saved = True
        yield ChatEvent("error", {"message": message, "code": code})
    except Exception:
        message = "The hotel chat could not complete this request. Try again."
        save_stage(database_path, started.conversation_id, started.turn_id,
                   "error", {"message": message, "code": "retryable"})
        error_saved = True
        yield ChatEvent("error", {"message": message, "code": "retryable"})
    finally:
        if not completed and not error_saved:
            save_stage(database_path, started.conversation_id, started.turn_id,
                       "error", {"message": "The chat request was interrupted."})
