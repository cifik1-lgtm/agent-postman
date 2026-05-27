"""
Replayer — Replay a previously captured workflow step-by-step.
Loads from the message store or a saved JSONL file.
"""
import json
import time
from pathlib import Path
from . import store
from . import tester


def replay_from_store(start_id: int = 1, end_id: int = None,
                      delay_ms: int = 500) -> list[dict]:
    """
    Replay all messages in the store between start_id and end_id.
    For HTTP messages (with a 'to' URL), re-fires the actual request.
    Returns list of replay results.
    """
    messages = store.all_messages()
    results = []
    for msg in messages:
        mid = msg.get("id", 0)
        if mid < start_id:
            continue
        if end_id and mid > end_id:
            break

        # If this was a real HTTP call, replay it
        if msg.get("to", "").startswith("http") and msg.get("payload"):
            result = tester.call_endpoint(
                url=msg["to"],
                payload=msg["payload"],
                method=msg.get("method", "POST"),
            )
            results.append({"replayed_id": mid, "result": result})
        else:
            # Non-HTTP message — just echo it back into store
            replayed = dict(msg)
            replayed.pop("id", None)
            replayed.pop("timestamp", None)
            replayed["replayed_from"] = mid
            store.append(replayed)
            results.append({"replayed_id": mid, "result": replayed})

        if delay_ms > 0:
            time.sleep(delay_ms / 1000)

    return results


def replay_from_file(filepath: str, delay_ms: int = 300) -> list[dict]:
    """Replay messages from a saved JSONL workflow file."""
    path = Path(filepath)
    if not path.exists():
        return [{"error": f"File not found: {filepath}"}]

    results = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
            if msg.get("to", "").startswith("http") and msg.get("payload"):
                result = tester.call_endpoint(
                    url=msg["to"],
                    payload=msg["payload"],
                    method=msg.get("method", "POST"),
                )
                results.append(result)
            else:
                store.append(msg)
                results.append(msg)
        except Exception as e:
            results.append({"error": str(e), "line": line[:80]})
        if delay_ms > 0:
            time.sleep(delay_ms / 1000)

    return results


def save_workflow(name: str, start_id: int = 1, end_id: int = None) -> str:
    """Save a slice of the current message store as a named workflow JSONL file."""
    messages = store.all_messages()
    out_dir = Path(__file__).parent.parent / "workflows"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"{name}.jsonl"

    with open(out_path, "w", encoding="utf-8") as f:
        for msg in messages:
            mid = msg.get("id", 0)
            if mid < start_id:
                continue
            if end_id and mid > end_id:
                break
            f.write(json.dumps(msg) + "\n")

    return str(out_path)
