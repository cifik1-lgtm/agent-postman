"""
Shared in-memory store for all captured agent messages.
Thread-safe. Persists to disk as JSONL for replay.
"""
import json
import threading
from datetime import datetime
from pathlib import Path

STORE_PATH = Path(__file__).parent.parent / "logs" / "messages.jsonl"
STORE_PATH.parent.mkdir(exist_ok=True)

_lock = threading.Lock()
_messages: list[dict] = []

# Load existing logs on startup
if STORE_PATH.exists():
    try:
        for line in STORE_PATH.read_text(encoding="utf-8").splitlines():
            if line.strip():
                _messages.append(json.loads(line))
    except Exception:
        pass


def append(msg: dict) -> dict:
    msg.setdefault("id", len(_messages) + 1)
    msg.setdefault("timestamp", datetime.now().isoformat())
    with _lock:
        _messages.append(msg)
        with open(STORE_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(msg) + "\n")
    return msg


def all_messages() -> list[dict]:
    with _lock:
        return list(_messages)


def get_by_id(msg_id: int) -> dict | None:
    with _lock:
        for m in _messages:
            if m.get("id") == msg_id:
                return m
    return None


def clear():
    with _lock:
        _messages.clear()
    STORE_PATH.write_text("", encoding="utf-8")
