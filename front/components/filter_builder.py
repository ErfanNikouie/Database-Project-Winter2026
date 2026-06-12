from __future__ import annotations

from typing import Any


def build_filter_payload(fields: list[dict[str, Any]], values: dict[str, Any]) -> dict[str, Any]:
    field_names = {field["name"] for field in fields}
    payload: dict[str, Any] = {}
    for key, value in values.items():
        if key not in field_names:
            continue
        if value in (None, ""):
            continue
        payload[key] = value
    return payload

