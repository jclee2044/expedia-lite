"""Application-owned conversation and retrieval trace writes."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from backend.controllers.database import connect_database
from backend.models.chat import ConversationHistory, StoredChatMessage
from backend.models.retrieval import StayRequest

PROMPT_VERSION = "5"


class ConversationNotFoundError(ValueError):
    """An opaque conversation identifier has no saved record."""


@dataclass(frozen=True)
class StartedTurn:
    conversation_id: str
    turn_id: str
    previous_messages: tuple[StoredChatMessage, ...]
    previous_request: StayRequest | None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _messages(connection: sqlite3.Connection, conversation_id: str) -> tuple[StoredChatMessage, ...]:
    rows = connection.execute(
        """
        SELECT turn_id, role, content, created_at_utc
        FROM chat_messages WHERE conversation_id = ? ORDER BY message_id
        """, (conversation_id,),
    ).fetchall()
    return tuple(StoredChatMessage(**dict(row)) for row in rows)


def _previous_request(connection: sqlite3.Connection, conversation_id: str) -> StayRequest | None:
    row = connection.execute(
        """
        SELECT detail_json FROM chat_retrieval_stages
        WHERE conversation_id = ? AND stage = 'result'
        ORDER BY stage_id DESC LIMIT 1
        """, (conversation_id,),
    ).fetchone()
    if row is None:
        return None
    request = json.loads(row["detail_json"]).get("request")
    if not isinstance(request, dict):
        return None
    return StayRequest(**request)


def start_turn(database_path: Path, conversation_id: str | None, question: str) -> StartedTurn:
    """Create a conversation if needed, then save the user's question."""
    connection = connect_database(database_path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        if conversation_id is None:
            conversation_id = str(uuid4())
            now = _now()
            connection.execute(
                "INSERT INTO chat_conversations VALUES (?, ?, ?)",
                (conversation_id, now, now),
            )
        elif connection.execute(
            "SELECT 1 FROM chat_conversations WHERE conversation_id = ?",
            (conversation_id,),
        ).fetchone() is None:
            raise ConversationNotFoundError("Chat history was not found. Start a new chat.")
        previous_messages = _messages(connection, conversation_id)
        previous_request = _previous_request(connection, conversation_id)
        turn_id = str(uuid4())
        connection.execute(
            """
            INSERT INTO chat_messages (conversation_id, turn_id, role, content, created_at_utc)
            VALUES (?, ?, 'user', ?, ?)
            """, (conversation_id, turn_id, question, _now()),
        )
        connection.execute(
            "UPDATE chat_conversations SET updated_at_utc = ? WHERE conversation_id = ?",
            (_now(), conversation_id),
        )
        connection.commit()
        return StartedTurn(conversation_id, turn_id, previous_messages, previous_request)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def save_stage(
    database_path: Path, conversation_id: str, turn_id: str,
    stage: str, detail: dict[str, object],
) -> None:
    """Write one labeled trace stage independently of proposed read-only SQL."""
    if stage not in {"proposal", "execution", "result", "error"}:
        raise ValueError("Unknown retrieval stage.")
    connection = connect_database(database_path)
    try:
        connection.execute(
            """
            INSERT INTO chat_retrieval_stages
                (conversation_id, turn_id, stage, detail_json, prompt_version, created_at_utc)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (conversation_id, turn_id, stage, json.dumps(detail, ensure_ascii=False),
                  PROMPT_VERSION, _now()),
        )
        connection.commit()
    finally:
        connection.close()


def save_assistant(
    database_path: Path, conversation_id: str, turn_id: str, content: str,
    recommendation: dict[str, object] | None = None,
) -> None:
    """Store only a fully completed assistant reply."""
    connection = connect_database(database_path)
    try:
        if recommendation is not None:
            row = connection.execute(
                "SELECT stage_id, detail_json FROM chat_retrieval_stages "
                "WHERE conversation_id = ? AND turn_id = ? AND stage = 'result' "
                "ORDER BY stage_id DESC LIMIT 1", (conversation_id, turn_id),
            ).fetchone()
            if row is None:
                raise ValueError("Checked retrieval trace is missing.")
            detail = json.loads(row["detail_json"])
            detail["second_model_answer"] = recommendation
            detail["answer_validation"] = "passed; facts rendered from checked records"
            connection.execute(
                "UPDATE chat_retrieval_stages SET detail_json = ? WHERE stage_id = ?",
                (json.dumps(detail, ensure_ascii=False), row["stage_id"]),
            )
        connection.execute(
            """
            INSERT INTO chat_messages (conversation_id, turn_id, role, content, created_at_utc)
            VALUES (?, ?, 'assistant', ?, ?)
            """, (conversation_id, turn_id, content, _now()),
        )
        connection.execute(
            "UPDATE chat_conversations SET updated_at_utc = ? WHERE conversation_id = ?",
            (_now(), conversation_id),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def load_history(database_path: Path, conversation_id: str) -> ConversationHistory:
    """Read saved messages and the most recent failed-turn message, if any."""
    connection = connect_database(database_path)
    try:
        if connection.execute(
            "SELECT 1 FROM chat_conversations WHERE conversation_id = ?",
            (conversation_id,),
        ).fetchone() is None:
            raise ConversationNotFoundError("Chat history was not found. Start a new chat.")
        messages = _messages(connection, conversation_id)
        last_error = None
        last_error_code = None
        if messages and messages[-1].role == "user":
            row = connection.execute(
                """
                SELECT detail_json FROM chat_retrieval_stages
                WHERE conversation_id = ? AND turn_id = ? AND stage = 'error'
                ORDER BY stage_id DESC LIMIT 1
                """, (conversation_id, messages[-1].turn_id),
            ).fetchone()
            if row is not None:
                detail = json.loads(row["detail_json"])
                last_error = detail.get("message")
                last_error_code = detail.get("code")
        return ConversationHistory(conversation_id, messages, last_error, last_error_code)
    finally:
        connection.close()
