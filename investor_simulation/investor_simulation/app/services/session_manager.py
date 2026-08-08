"""
In-memory session manager.

Per section 11/20 of the spec, this is a hackathon MVP: no database, no Redis.
A simple process-wide dict keyed by session_id is enough. The SessionState
pydantic model (app/models/schemas.py) is the single source of truth for
conversation state - the LLM is never trusted to "remember" anything itself.
"""

from __future__ import annotations

import os
import threading
from typing import Dict, Optional

from app.models.schemas import SessionState, VulnerabilityMap

DEFAULT_MAX_ROUNDS = int(os.environ.get("MAX_ROUNDS", "8"))


class SessionNotFoundError(Exception):
    pass


class SessionAlreadyExistsError(Exception):
    pass


class SessionManager:
    """Thread-safe in-memory store for investor-simulation sessions."""

    def __init__(self) -> None:
        self._sessions: Dict[str, SessionState] = {}
        self._lock = threading.Lock()

    def create_session(
        self,
        session_id: str,
        startup_id: str,
        refined_pitch: str,
        vulnerability_map: VulnerabilityMap,
        founder_concerns: list,
        max_rounds: Optional[int] = None,
    ) -> SessionState:
        with self._lock:
            if session_id in self._sessions:
                raise SessionAlreadyExistsError(
                    f"Session '{session_id}' already exists."
                )
            state = SessionState(
                session_id=session_id,
                startup_id=startup_id,
                refined_pitch=refined_pitch,
                vulnerability_map=vulnerability_map,
                founder_concerns=founder_concerns,
                max_rounds=max_rounds or DEFAULT_MAX_ROUNDS,
            )
            self._sessions[session_id] = state
            return state

    def get(self, session_id: str) -> SessionState:
        with self._lock:
            state = self._sessions.get(session_id)
            if state is None:
                raise SessionNotFoundError(f"Session '{session_id}' not found.")
            return state

    def save(self, state: SessionState) -> None:
        with self._lock:
            self._sessions[state.session_id] = state

    def delete(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)

    def all_session_ids(self):
        with self._lock:
            return list(self._sessions.keys())


_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    global _manager
    if _manager is None:
        _manager = SessionManager()
    return _manager
