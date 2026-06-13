from __future__ import annotations

from typing import Any

import dash_mantine_components as dmc
from dash import html

from utils.labels import humanize_field_name


def build_dynamic_form(
    *,
    form_key: str,
    fields: list[dict[str, Any]],
    initial_data: dict[str, Any] | None = None,
    fk_options_by_field: dict[str, list[dict[str, str]]] | None = None,
    lookup_options_by_field: dict[str, list[dict[str, str]]] | None = None,
    mode: str = "insert",
) -> html.Div:
    controls: list[Any] = []
    initial = initial_data or {}
    system_fields = {"id", "created_at", "updated_at"}
    fk_options = fk_options_by_field or {}
    lookup_options = lookup_options_by_field or {}

    for field in fields:
        name = field["name"]
        is_locked = name in system_fields and mode == "insert"
        required = bool(field.get("required")) and not is_locked
        label = humanize_field_name(name)
        value = initial.get(name)
        component_id = {"type": f"form-field-{form_key}", "name": name}
        description = []
        if is_locked:
            description.append("system")
        if field.get("unique"):
            description.append("unique")
        if name == "password_hash":
            description.append("required")
            if mode == "edit":
                description.append("use __EMPTY__ to reset on next login")
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

        if field["type"] == "ForeignKey":
            select_value = None if value in (None, "") else str(value)
            select_data = _with_current_value_option(
                _sort_options_by_id(fk_options.get(name, [])),
                select_value,
            )
            control = dmc.Select(
                id=component_id,
                label=label,
                data=select_data,
                value=select_value,
                searchable=True,
                clearable=True,
                required=required,
                description=desc_text,
            )
        elif field["type"] == "Lookup":
            select_value = None if value in (None, "") else str(value)
            select_data = _with_current_value_option(
                _sort_options_by_id(lookup_options.get(name, [])),
                select_value,
            )
            control = dmc.Select(
                id=component_id,
                label=label,
                data=select_data,
                value=select_value,
                searchable=True,
                clearable=True,
                required=required,
                description=desc_text,
            )
        elif field["type"] == "String":
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


def _sort_options_by_id(options: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def key_fn(option: dict[str, Any]) -> tuple[int, int | str]:
        raw_value = option.get("value")
        try:
            return (0, int(float(str(raw_value))))
        except (TypeError, ValueError):
            return (1, str(raw_value or ""))

    return sorted(options, key=key_fn)


def _with_current_value_option(options: list[dict[str, Any]], current_value: str | None) -> list[dict[str, Any]]:
    if current_value in (None, ""):
        return options
    normalized = str(current_value)
    if any(str(option.get("value")) == normalized for option in options):
        return options
    return [{"value": normalized, "label": normalized}, *options]


