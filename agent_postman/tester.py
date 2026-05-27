"""
Tester — Fire HTTP/JSON requests to agent skill endpoints.
Like Postman but for agent tool APIs.
"""
import json
import time
import urllib.request
import urllib.error
from . import store


def call_endpoint(url: str, payload: dict, method: str = "POST",
                  headers: dict = None, timeout: int = 10) -> dict:
    """
    Call an agent skill/endpoint and return structured result.
    Records the call in the message store for inspection.
    """
    headers = headers or {"Content-Type": "application/json"}
    data = json.dumps(payload).encode("utf-8")

    result = {
        "from": "agent_postman",
        "to": url,
        "payload": payload,
        "method": method,
    }

    t0 = time.perf_counter()
    try:
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            elapsed = round((time.perf_counter() - t0) * 1000, 1)
            try:
                response_data = json.loads(body)
            except Exception:
                response_data = {"raw": body}
            result.update({
                "status": "ok",
                "http_status": resp.status,
                "response": response_data,
                "elapsed_ms": elapsed,
            })
    except urllib.error.HTTPError as e:
        elapsed = round((time.perf_counter() - t0) * 1000, 1)
        result.update({
            "status": "error",
            "http_status": e.code,
            "response": {"error": str(e)},
            "elapsed_ms": elapsed,
        })
    except Exception as e:
        elapsed = round((time.perf_counter() - t0) * 1000, 1)
        result.update({
            "status": "error",
            "http_status": 0,
            "response": {"error": str(e)},
            "elapsed_ms": elapsed,
        })

    store.append(result)
    return result


def ping(url: str, timeout: int = 5) -> dict:
    """Quick GET ping to check if an agent endpoint is alive."""
    result = {"from": "agent_postman", "to": url, "method": "GET"}
    t0 = time.perf_counter()
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = round((time.perf_counter() - t0) * 1000, 1)
            result.update({"status": "ok", "http_status": resp.status,
                           "elapsed_ms": elapsed})
    except Exception as e:
        elapsed = round((time.perf_counter() - t0) * 1000, 1)
        result.update({"status": "error", "http_status": 0,
                       "elapsed_ms": elapsed, "error": str(e)})
    store.append(result)
    return result
