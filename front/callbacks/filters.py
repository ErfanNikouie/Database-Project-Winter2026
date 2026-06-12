from __future__ import annotations

import re
from typing import Any

from dash import Input, Output, State, callback, no_update


_SIMPLE_NUMERIC_PATTERN = re.compile(r"^[0-9()\s<>=!&|.,+-]+$")


@callback(
    Output("dynamic-page-error", "children", allow_duplicate=True),
    Input({"type": "filter-field", "name": "ALL"}, "value"),
    State("schema-store", "data"),
    prevent_initial_call=True,
)
def validate_filters(values: list[Any], schema: dict):
    fields = schema.get("fields", []) if schema else []
    for field, value in zip(fields, values):
        if value in (None, ""):
            continue
        field_type = field.get("type")
        if field_type in {"Integer", "Double", "Decimal", "Date", "DateTime", "ForeignKey"}:
            if not _SIMPLE_NUMERIC_PATTERN.match(str(value)):
                return f"Invalid filter syntax for {field['name']}"
        if field_type == "Boolean" and str(value) not in {"True", "False"}:
            return f"Boolean filter for {field['name']} must be True or False"
    return no_update

