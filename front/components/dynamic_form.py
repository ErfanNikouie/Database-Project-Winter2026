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
    system_fields = {"id", "created_at", "updated_at", "password_hash"}

    for field in fields:
        name = field["name"]
        is_locked = name in system_fields
        required = bool(field.get("required")) and not is_locked
        label = f"{name}{' *' if required else ''}"
        value = initial.get(name)
        component_id = {"type": f"form-field-{form_key}", "name": name}
        description = []
        if is_locked:
            description.append("system")
        if field.get("unique"):
            description.append("unique")
        desc_text = " | ".join(description) if description else None

        if is_locked:
            controls.append(
                dmc.TextInput(
                    id=component_id,
                    label=label,
                    value="Auto generated",
                    disabled=True,
                    description=desc_text,
                )
            )
            continue

        if field["type"] in {"String", "ForeignKey", "Lookup"}:
            control = dmc.TextInput(id=component_id, label=label, value=value, required=required, description=desc_text)
        elif field["type"] == "Text":
            control = dmc.Textarea(id=component_id, label=label, value=value, required=required, description=desc_text)
        elif field["type"] in {"Integer", "Double", "Decimal"}:
            control = dmc.NumberInput(id=component_id, label=label, value=value, required=required, description=desc_text)
        elif field["type"] == "Boolean":
            control = dmc.Select(
                id=component_id,
                label=label,
                data=[
                    {"value": "", "label": "Select"},
                    {"value": "True", "label": "True"},
                    {"value": "False", "label": "False"},
                ],
                value="" if value in (None, "") else str(value),
                required=required,
                description=desc_text,
            )
        elif field["type"] == "Date":
            control = dmc.DateInput(id=component_id, label=label, value=value, required=required, description=desc_text)
        elif field["type"] == "DateTime":
            control = dmc.DateTimePicker(id=component_id, label=label, value=value, required=required, description=desc_text)
        else:
            control = dmc.TextInput(id=component_id, label=label, value=value, required=required, description=desc_text)

        controls.append(control)

    return html.Div(controls, className="dynamic-form-grid")

