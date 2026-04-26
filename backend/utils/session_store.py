# session_store.py
# In-memory session store for the Skill Assessment Agent.
# Stores full SessionState objects keyed by session_id (UUID).
# Thread-safe for single-server use. Replace with Redis for production scale.

import uuid
from datetime import datetime, timedelta
from typing import Optional
from backend.models.schemas import SessionState


# In-memory store: { session_id: (SessionState, last_accessed_time) }
_store: dict[str, tuple[SessionState, datetime]] = {}

# Sessions expire after 4 hours of inactivity (hackathon demo use case)
SESSION_TTL_HOURS = 4


def create_session() -> str:
    """Create a new session and return its ID."""
    session_id = str(uuid.uuid4())
    _store[session_id] = (SessionState(session_id=session_id), datetime.utcnow())
    _cleanup_expired()
    return session_id


def get_session(session_id: str) -> Optional[SessionState]:
    """Retrieve a session by ID. Returns None if not found or expired."""
    entry = _store.get(session_id)
    if entry is None:
        return None
    state, last_accessed = entry
    if datetime.utcnow() - last_accessed > timedelta(hours=SESSION_TTL_HOURS):
        del _store[session_id]
        return None
    return state


def save_session(state: SessionState) -> None:
    """Save/update a session state."""
    _store[state.session_id] = (state, datetime.utcnow())


def delete_session(session_id: str) -> None:
    """Delete a session."""
    _store.pop(session_id, None)


def list_active_sessions() -> list[str]:
    """Return all active (non-expired) session IDs."""
    _cleanup_expired()
    return list(_store.keys())


def _cleanup_expired() -> None:
    """Remove sessions that have exceeded the TTL."""
    cutoff = datetime.utcnow() - timedelta(hours=SESSION_TTL_HOURS)
    expired = [sid for sid, (_, ts) in _store.items() if ts < cutoff]
    for sid in expired:
        del _store[sid]
