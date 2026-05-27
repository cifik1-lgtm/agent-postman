"""
Validator — Validate agent payloads against a schema.
Uses simple dict-based schemas (no external dependencies needed).
"""
from . import store


def validate(payload: dict, schema: dict) -> dict:
    """
    Validate a payload against a schema dict.
    Schema format:
        {
          "field_name": {"type": str, "required": True, "min": 1, "max": 100},
          ...
        }
    Returns: {"valid": bool, "errors": [...]}
    """
    errors = []

    for field, rules in schema.items():
        value = payload.get(field)
        required = rules.get("required", False)
        expected_type = rules.get("type")

        if value is None:
            if required:
                errors.append(f"'{field}' is required but missing.")
            continue

        if expected_type and not isinstance(value, expected_type):
            errors.append(
                f"'{field}' must be {expected_type.__name__}, "
                f"got {type(value).__name__}."
            )
            continue

        if isinstance(value, str):
            min_len = rules.get("min")
            max_len = rules.get("max")
            if min_len is not None and len(value) < min_len:
                errors.append(f"'{field}' too short (min {min_len} chars).")
            if max_len is not None and len(value) > max_len:
                errors.append(f"'{field}' too long (max {max_len} chars).")

        if isinstance(value, (int, float)):
            min_val = rules.get("min")
            max_val = rules.get("max")
            if min_val is not None and value < min_val:
                errors.append(f"'{field}' below minimum ({min_val}).")
            if max_val is not None and value > max_val:
                errors.append(f"'{field}' above maximum ({max_val}).")

        allowed = rules.get("allowed")
        if allowed and value not in allowed:
            errors.append(f"'{field}' must be one of {allowed}, got '{value}'.")

    result = {"valid": len(errors) == 0, "errors": errors, "payload": payload}

    store.append({
        "from": "validator",
        "to": "schema_check",
        "payload": payload,
        "status": "valid" if result["valid"] else "invalid",
        "errors": errors,
    })

    return result


# --- Built-in schemas for common agent message types ---

AGENT_TOOL_CALL_SCHEMA = {
    "name":      {"type": str, "required": True, "min": 1, "max": 100},
    "args":      {"type": dict, "required": True},
}

AGENT_RESPONSE_SCHEMA = {
    "result":    {"type": str, "required": True},
}

HTTP_ENDPOINT_SCHEMA = {
    "url":       {"type": str, "required": True, "min": 7},
    "method":    {"type": str, "required": False, "allowed": ["GET", "POST", "PUT", "DELETE"]},
    "payload":   {"type": dict, "required": False},
}
