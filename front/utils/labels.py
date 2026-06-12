from __future__ import annotations


def humanize_field_name(name: str) -> str:
    """Convert snake_case (and backend suffixes) to user-facing labels."""
    value = (name or "").strip()
    if not value:
        return ""

    if value.endswith("__label"):
        value = value[: -len("__label")]
        if value.endswith("_id"):
            value = value[:-3]

    return value.replace("_", " ").strip().title()

