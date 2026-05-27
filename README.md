# Agent Postman 🔭

> **Postman + tcpdump + logs — but for AI agents.**

[![PyPI](https://img.shields.io/pypi/v/agent-postman)](https://pypi.org/project/agent-postman/)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

Are you debugging a multi-agent AI system and feeling like you're flying blind?

Single-agent setups are manageable. Multi-agent systems feel like debugging distributed systems with **invisible reasoning**.

**Agent Postman** is the terminal-native debugging toolkit you've been wishing existed.

```
╔══════════════════════════════════════════════════════════╗
║   🔭  AGENT POSTMAN  —  Postman for AI Agents  v1.0.0   ║
║      Inspect · Test · Replay · Simulate · Trace          ║
╚══════════════════════════════════════════════════════════╝

Commands:
  1 · inspect          Browse all captured agent messages
  2 · test             Fire a request to an agent endpoint
  3 · replay           Replay a saved workflow
  4 · simulate         Simulate another agent sending messages
  5 · validate         Validate a payload against a schema
  6 · trace            Live-trace all agent traffic (Ctrl+C to stop)
  7 · summary          Show traffic summary stats
  8 · inject           Manually inject a test message
  q · quit
```

---

## 🚀 Install

```bash
pip install agent-postman
agent-postman
```

That's it. No config. No cloud. Runs entirely on your machine.

---

## ✨ Features

### 🔍 Inspect Agent Messages
See every message your agents sent and received — who sent it, who received it, the full payload, status, and timestamp.

```
  #1  18:31:00  planner_agent     →  executor_agent           ✓ ok
  #2  18:31:00  executor_agent    →  http://api/search        ✓ ok
  #3  18:31:00  executor_agent    →  http://broken-api/call   ✗ error
```

### ⚡ Test Skill Endpoints
Fire real HTTP requests to any agent skill endpoint — like Postman, but from your terminal.

```bash
agent-postman test http://localhost:8000/api/tool '{"name":"web_search","args":{"q":"AI"}}'
```

### 🔁 Replay Workflows
Captured a bug? Save the message sequence as a workflow file and replay it exactly — step by step, with configurable delays.

### 🤖 Simulate Other Agents
Test how your agent handles inputs from another agent — without needing the second agent running. Includes a **flood tester** for rate-limit and stability testing.

### ✅ Validate Payloads
Catch schema violations before they hit production. Built-in schemas for tool calls, agent responses, and HTTP endpoints.

```python
result = validator.validate(payload, AGENT_TOOL_CALL_SCHEMA)
# {"valid": False, "errors": ["'name' is required but missing."]}
```

### 📡 Live Trace
Watch agent traffic in real time — like `tcpdump` for your AI system. Every new message prints instantly. Failures highlighted in red.

```
[18:31:05] planner_agent → executor_agent         ✓ ok   (12ms)
[18:31:05] executor_agent → http://api/search     ✓ ok   (234ms)
[18:31:06] router → http://broken-api.com         ✗ error (150ms)
```

---

## 📖 Usage

### Interactive mode
```bash
agent-postman
```

### CLI mode (for scripting)
```bash
# Test an endpoint
agent-postman test http://localhost:8000/tools '{"name":"search","args":{}}'

# Get traffic summary
agent-postman summary

# Live trace
agent-postman trace

# Validate a payload
agent-postman validate '{"name":"search","args":{"q":"test"}}'
```

### Python API
```python
from agent_postman import inspector, tester, tracer, validator

# Fire a request
result = tester.call_endpoint("http://localhost:8000/api/tool", {"name": "search"})

# Validate a payload
v = validator.validate(payload, validator.AGENT_TOOL_CALL_SCHEMA)

# Get all failures
failures = tracer.get_failures()

# Get traffic summary
summary = tracer.summarize()
```

---

## 🗂 Project Structure

```
agent_postman/
├── inspector.py   # Browse & inspect agent messages
├── tester.py      # Fire HTTP requests to endpoints
├── replayer.py    # Replay saved workflows
├── simulator.py   # Simulate agents, flood tests
├── validator.py   # Schema validation
├── tracer.py      # Live trace, failure detection
└── store.py       # Thread-safe persistent message store
```

---

## 💰 Pricing

**100% Free and Open Source.** 

This was built by a developer frustrated with multi-agent debugging. All features (including live tracing, simulation, and workflow replay) are completely unlocked. If it saves you hours of debugging, just drop a star on the repo!

---

## 🛠 Requirements

- Python 3.10+
- `rich` (auto-installed)
- No cloud. No API keys. No subscriptions.

---

## 📝 License

MIT — free to use, fork, and modify.

---

*Built for developers who are tired of debugging AI agents with `print()` statements.*
