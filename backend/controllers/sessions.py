"""Dependency-free, process-local login session storage."""

from __future__ import annotations

import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True)
class _Session:
    user_id: str
    expires_at: float


class SessionStore:
    """Track opaque session tokens with bounded lifetimes."""

    def __init__(
        self,
        lifetime_seconds: int = 8 * 60 * 60,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.lifetime_seconds = lifetime_seconds
        self._clock = clock
        self._sessions: dict[str, _Session] = {}
        self._lock = Lock()

    def create(self, user_id: str) -> str:
        """Create and return a cryptographically random session token."""
        token = secrets.token_urlsafe(32)
        now = self._clock()
        with self._lock:
            self._remove_expired(now)
            self._sessions[token] = _Session(
                user_id=user_id,
                expires_at=now + self.lifetime_seconds,
            )
        return token

    def resolve(self, token: str | None) -> str | None:
        """Resolve a live token to its user ID, removing expired sessions."""
        if not token:
            return None
        now = self._clock()
        with self._lock:
            self._remove_expired(now)
            session = self._sessions.get(token)
            return session.user_id if session is not None else None

    def invalidate(self, token: str | None) -> None:
        """Invalidate one token if it exists."""
        if not token:
            return
        with self._lock:
            self._sessions.pop(token, None)

    def _remove_expired(self, now: float) -> None:
        expired = [
            token
            for token, session in self._sessions.items()
            if session.expires_at <= now
        ]
        for token in expired:
            self._sessions.pop(token, None)
