"""Framework-free persisted chat read objects."""

from dataclasses import dataclass


@dataclass(frozen=True)
class StoredChatMessage:
    turn_id: str
    role: str
    content: str
    created_at_utc: str


@dataclass(frozen=True)
class ConversationHistory:
    conversation_id: str
    messages: tuple[StoredChatMessage, ...]
    last_error: str | None
    last_error_code: str | None
