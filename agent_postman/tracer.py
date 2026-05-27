"""
Tracer — Live trace of agent failures, errors, and message flow.
Acts like tcpdump but for agent message traffic.
"""
import threading
import time
from datetime import datetime
from . import store


_trace_active = False
_trace_thread = None
_seen_ids: set[int] = set()
_listeners: list = []


def add_listener(fn):
    """Register a callback fn(msg) that gets called for each new message."""
    _listeners.append(fn)


def remove_listener(fn):
    if fn in _listeners:
        _listeners.remove(fn)


def _tracer_loop(poll_interval: float = 0.5):
    global _trace_active
    while _trace_active:
        msgs = store.all_messages()
        for msg in msgs:
            mid = msg.get("id")
            if mid not in _seen_ids:
                _seen_ids.add(mid)
                for fn in _listeners:
                    try:
                        fn(msg)
                    except Exception:
                        pass
        time.sleep(poll_interval)


def start_trace(on_message=None):
    """
    Start live tracing. Optional callback on_message(msg) fires for each new message.
    """
    global _trace_active, _trace_thread
    if _trace_active:
        return

    if on_message:
        add_listener(on_message)

    _trace_active = True
    _trace_thread = threading.Thread(target=_tracer_loop, daemon=True,
                                     name="AgentPostmanTracer")
    _trace_thread.start()


def stop_trace():
    global _trace_active
    _trace_active = False


def get_failures(last_n: int = 50) -> list[dict]:
    """Return only messages where status == 'error' or 'invalid'."""
    msgs = store.all_messages()
    failures = [m for m in msgs
                if m.get("status") in ("error", "invalid", "failed")]
    return failures[-last_n:]


def get_slow_calls(threshold_ms: float = 1000.0) -> list[dict]:
    """Return messages that took longer than threshold_ms."""
    msgs = store.all_messages()
    return [m for m in msgs
            if isinstance(m.get("elapsed_ms"), (int, float))
            and m["elapsed_ms"] > threshold_ms]


def summarize() -> dict:
    """Return a quick summary of all message traffic."""
    msgs = store.all_messages()
    total = len(msgs)
    ok = sum(1 for m in msgs if m.get("status") == "ok")
    errors = sum(1 for m in msgs if m.get("status") in ("error", "invalid"))
    avg_ms_list = [m["elapsed_ms"] for m in msgs
                   if isinstance(m.get("elapsed_ms"), (int, float))]
    avg_ms = round(sum(avg_ms_list) / len(avg_ms_list), 1) if avg_ms_list else 0
    return {
        "total_messages": total,
        "ok": ok,
        "errors": errors,
        "avg_response_ms": avg_ms,
        "unique_endpoints": len(set(m.get("to", "") for m in msgs)),
    }
