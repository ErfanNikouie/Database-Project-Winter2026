import re

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def safe_identifier(value: str, *, label: str = "identifier") -> str:
    """Validate that `value` is a safe SQL identifier (SQLite compatible).

    Prevents SQL injection and accidental quoting problems for dynamic table/column names.

    Allowed: letters, numbers, underscore; must not start with a number.
    """
    if value is None:
        raise ValueError(f"{label} cannot be None")
    value = value.strip()
    if not value:
        raise ValueError(f"{label} cannot be empty")
    if not _IDENTIFIER_RE.match(value):
        raise ValueError(
            f"Invalid {label} '{value}'. Use only letters, numbers and underscore; cannot start with a number."
        )
    return value

