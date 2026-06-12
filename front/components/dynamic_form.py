from __future__ import annotations

from typing import Any

import dash_mantine_components as dmc
from dash import html


def build_dynamic_form(
    *,
    form_key: str,
    fields: list[dict[str, Any]],
    initial_data: dict[str, Any] | None = None,
) -> html.Div:
    controls: list[Any] = []
    initial = initial_data or {}

    for field in fields:
        name = field["name"]
        if name in {"id", "created_at", "updated_at", "password_hash"}:
            continue

        label = f"{name}{' *' if field.get('required') else ''}"
        value = initial.get(name)
        component_id = {"type": f"form-field-{form_key}", "name": name}

        if field["type"] in {"String", "ForeignKey", "Lookup"}:
            control = dmc.TextInput(id=component_id, label=label, value=value)
        elif field["type"] == "Text":
            control = dmc.Textarea(id=component_id, label=label, value=value)
        elif field["type"] in {"Integer", "Double", "Decimal"}:
            control = dmc.NumberInput(id=component_id, label=label, value=value)
        elif field["type"] == "Boolean":
            control = dmc.Select(
                id=component_id,
                label=label,
                data=[
                    {"value": "", "label": "Don't Care"},
                    {"value": "True", "label": "True"},
                    {"value": "False", "label": "False"},
                ],
                value="" if value in (None, "") else str(value),
            )
        elif field["type"] == "Date":
            control = dmc.DateInput(id=component_id, label=label, value=value)
        elif field["type"] == "DateTime":
            control = dmc.DateTimePicker(id=component_id, label=label, value=value)
        else:
            control = dmc.TextInput(id=component_id, label=label, value=value)

        controls.append(control)

    return html.Div(controls, className="dynamic-form-grid")

