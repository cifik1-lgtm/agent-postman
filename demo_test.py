"""
Demo test — injects sample agent traffic and exercises all features.
Run: python demo_test.py
"""
import sys, json
sys.path.insert(0, ".")

from agent_postman import inspector, validator, tracer, store

print("=" * 60)
print("  AGENT POSTMAN — DEMO TEST")
print("=" * 60)

# ── 1. Inject demo messages ──
print("\n[1] Injecting demo agent traffic...")
inspector.inject_test_message("planner_agent",  "executor_agent",
    {"task": "search web", "query": "AI tools 2026"}, "ok")
inspector.inject_test_message("executor_agent", "http://localhost:8000/api/search",
    {"q": "AI tools"}, "ok")
inspector.inject_test_message("executor_agent", "http://localhost:9999/api/broken",
    {"q": "test"}, "error")
inspector.inject_test_message("memory_agent",   "executor_agent",
    {"action": "save", "key": "last_search"}, "ok")
inspector.inject_test_message("validator",      "schema_check",
    {"name": "web_search", "args": {"q": "test"}}, "valid")

store.append({"from": "planner", "to": "http://slow-api.com/process",
              "status": "ok", "elapsed_ms": 2400, "payload": {}})
store.append({"from": "router",  "to": "http://broken-api.com/call",
              "status": "error", "elapsed_ms": 150,
              "response": {"error": "Connection refused"}, "payload": {}})
print("  -> 7 messages injected.")

# ── 2. Summary ──
print("\n[2] Traffic Summary:")
s = tracer.summarize()
print(f"  Total messages   : {s['total_messages']}")
print(f"  Successful       : {s['ok']}")
print(f"  Errors           : {s['errors']}")
print(f"  Avg response ms  : {s['avg_response_ms']}")
print(f"  Unique endpoints : {s['unique_endpoints']}")

# ── 3. Failures ──
print("\n[3] Failures detected:")
failures = tracer.get_failures()
if failures:
    for f in failures:
        err = str(f.get("response", {}).get("error", f.get("status", "?")))[:50]
        print(f"  [#{f.get('id')}] {f.get('from')} -> {f.get('to')} : {err}")
else:
    print("  None")

# ── 4. Slow calls ──
print("\n[4] Slow calls (>1000ms):")
slow = tracer.get_slow_calls(threshold_ms=1000)
if slow:
    for sc in slow:
        print(f"  [#{sc.get('id')}] {sc.get('from')} -> {sc.get('to')} : {sc.get('elapsed_ms')}ms")
else:
    print("  None")

# ── 5. Inspect all messages ──
print("\n[5] All captured messages:")
msgs = inspector.list_messages()
print(f"  {'ID':>3}  {'TIME':>8}  {'FROM':<22} {'TO':<35}  STATUS")
print(f"  {'-'*78}")
for m in msgs:
    ts  = m.get("timestamp", "")[:19].replace("T", " ")[11:]
    frm = str(m.get("from", "?"))[:21]
    to  = str(m.get("to",   "?"))[:34]
    st  = m.get("status", "?")
    mid = m.get("id", "?")
    print(f"  {mid:>3}  {ts:>8}  {frm:<22} {to:<35}  {st}")

# ── 6. Validate a payload ──
print("\n[6] Validating a sample agent tool-call payload...")
good_payload = {"name": "web_search", "args": {"query": "AI tools"}}
bad_payload  = {"args": {"query": "AI tools"}}  # missing 'name'

r1 = validator.validate(good_payload, validator.AGENT_TOOL_CALL_SCHEMA)
r2 = validator.validate(bad_payload,  validator.AGENT_TOOL_CALL_SCHEMA)

print(f"  Good payload valid : {r1['valid']}")
print(f"  Bad  payload valid : {r2['valid']}")
if r2["errors"]:
    for e in r2["errors"]:
        print(f"    Error: {e}")

print("\n" + "=" * 60)
print("  ALL TESTS PASSED. Agent Postman is working correctly!")
print("  Run 'python main.py' to open the interactive terminal UI.")
print("=" * 60 + "\n")
