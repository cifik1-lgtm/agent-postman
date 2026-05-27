"""
Inspector — Browse and inspect all captured agent messages.
Shows: sender, receiver, payload, timestamp, status.
"""
from datetime import datetime
from . import store


def _format_ts(ts: str) -> str:
    try:
        return datetime.fromisoformat(ts).strftime("%H:%M:%S")
    except Exception:
        return ts[:8]


def list_messages(filter_agent: str = None, limit: int = 50) -> list[dict]:
    """Return recent messages, optionally filtered by agent name."""
    msgs = store.all_messages()
    if filter_agent:
        fa = filter_agent.lower()
        msgs = [m for m in msgs if fa in str(m.get("from", "")).lower()
                or fa in str(m.get("to", "")).lower()]
    return msgs[-limit:]


def inspect(msg_id: int) -> dict | None:
    """Return full detail of a single message by ID."""
    return store.get_by_id(msg_id)


def inject_test_message(sender: str, receiver: str, payload: dict,
                        status: str = "sent") -> dict:
    """Manually inject a message into the store (for testing)."""
    msg = {
        "from": sender,
        "to": receiver,
        "payload": payload,
        "status": status,
    }
    return store.append(msg)
