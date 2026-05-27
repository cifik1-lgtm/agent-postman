"""
Simulator — Simulate another agent sending messages to your agent.
Useful for testing how your agent handles different inputs
without needing a real second agent running.
"""
import json
import time
import random
from datetime import datetime
from . import store
from . import tester


def simulate_agent(
    agent_name: str,
    target_url: str,
    messages: list[dict],
    delay_ms: int = 500,
    randomize: bool = False,
) -> list[dict]:
    """
    Simulate 'agent_name' sending a list of messages to 'target_url'.
    Each message in the list should have a 'payload' key.
    Returns list of results.
    """
    if randomize:
        messages = random.sample(messages, len(messages))

    results = []
    for i, msg in enumerate(messages):
        payload = msg.get("payload", msg)
        print(f"  [{agent_name}] → [{target_url}] Sending message {i+1}/{len(messages)}...")
        result = tester.call_endpoint(
            url=target_url,
            payload=payload,
            method=msg.get("method", "POST"),
        )
        result["simulated_agent"] = agent_name
        results.append(result)
        if delay_ms > 0:
            time.sleep(delay_ms / 1000)

    return results


def simulate_conversation(
    agent_a: str,
    agent_b_url: str,
    turns: list[str],
    delay_ms: int = 800,
) -> list[dict]:
    """
    Simulate a back-and-forth conversation between two agents.
    'turns' is a list of text messages from agent_a to agent_b.
    """
    results = []
    for turn in turns:
        msg = {
            "from": agent_a,
            "message": turn,
            "timestamp": datetime.now().isoformat(),
        }
        result = tester.call_endpoint(
            url=agent_b_url,
            payload=msg,
        )
        result["turn"] = turn
        results.append(result)
        if delay_ms > 0:
            time.sleep(delay_ms / 1000)
    return results


def flood_test(
    target_url: str,
    payload: dict,
    count: int = 10,
    concurrency: int = 1,
) -> dict:
    """
    Fire 'count' identical messages at target_url to test rate limiting & stability.
    Returns summary stats.
    """
    import threading
    results = []
    errors = []
    lock = threading.Lock()

    def _fire():
        r = tester.call_endpoint(target_url, payload)
        with lock:
            if r.get("status") == "ok":
                results.append(r.get("elapsed_ms", 0))
            else:
                errors.append(r.get("response", {}).get("error", "unknown"))

    threads = []
    for _ in range(count):
        t = threading.Thread(target=_fire, daemon=True)
        threads.append(t)

    # Launch in batches of 'concurrency'
    for i in range(0, len(threads), concurrency):
        batch = threads[i:i + concurrency]
        for t in batch:
            t.start()
        for t in batch:
            t.join()

    avg_ms = round(sum(results) / len(results), 1) if results else 0
    return {
        "total": count,
        "success": len(results),
        "errors": len(errors),
        "avg_ms": avg_ms,
        "min_ms": min(results, default=0),
        "max_ms": max(results, default=0),
        "error_messages": errors[:5],
    }
