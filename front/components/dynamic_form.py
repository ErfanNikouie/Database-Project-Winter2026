from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

import streamlit as st

from services.metadata import load_foreign_key_options_cached, load_lookup_values_cached


def render_dynamic_form(
    *,
    base_url: str,
    access_token: str,
    form_name: str,
    fields: list[dict],
    initial_data: dict[str, Any] | None,
    scope_key: str,
    metadata_version: str,
) -> tuple[bool, dict[str, Any]]:
    payload: dict[str, Any] = {}
    submitted = False

    with st.form(key=f"dynamic-form-{scope_key}", clear_on_submit=False):
        for field in fields:
            name = field["name"]
            field_type = field["type"]
            required = field.get("required", False)
            if name in {"id", "created_at", "updated_at"}:
                continue
            label = f"{name}{' *' if required else ''}"
            value = _render_field_input(
                base_url=base_url,
                access_token=access_token,
                form_name=form_name,
                field=field,
                label=label,
                initial_value=(initial_data or {}).get(name),
                scope_key=scope_key,
                metadata_version=metadata_version,
            )
            if value is not None and value != "":
                payload[name] = value

        submitted = st.form_submit_button("Save", use_container_width=True)

    if initial_data and "id" in initial_data:
        payload["id"] = initial_data["id"]

    return submitted, payload


def _render_field_input(
    *,
    base_url: str,
    access_token: str,
    form_name: str,
    field: dict,
    label: str,
    initial_value: Any,
    scope_key: str,
    metadata_version: str,
):
    field_type = field["type"]
    key = f"{scope_key}-{form_name}-{field['name']}"

    if field_type in {"Integer", "ForeignKey", "Lookup"}:
        if field_type == "Lookup" and field.get("lookup_id"):
            lookup_query = st.text_input(
                f"{label} search",
                key=f"{key}-lookup-search",
                placeholder="Type lookup text",
            )
            lookup_items = load_lookup_values_cached(
                base_url,
                access_token,
                metadata_version,
                int(field["lookup_id"]),
                query=lookup_query,
                limit=100,
            )
            options = {item["id"]: item["value"] for item in lookup_items}
            initial_id = int(initial_value) if initial_value not in (None, "") else None
            if initial_id and initial_id not in options:
                options[initial_id] = str(initial_value)
            selected = st.selectbox(
                label,
                options=list(options.keys()),
                index=None if initial_id is None else list(options.keys()).index(initial_id) if initial_id in options else None,
                format_func=lambda lookup_id: f"{lookup_id} - {options[lookup_id]}",
                key=key,
            )
            return selected
        if field_type == "ForeignKey":
            foreign_table = field.get("foreign_key_table", "")
            search_query = st.text_input(
                f"{label} search",
                key=f"{key}-fk-search",
                placeholder="Type to search referenced records",
            )
            options_items = load_foreign_key_options_cached(
                base_url,
                access_token,
                metadata_version,
                foreign_table,
                search_query,
                50,
            )
            options = {int(item["id"]): str(item["label"]) for item in options_items}
            initial_id = int(initial_value) if initial_value not in (None, "") else None
            if initial_id and initial_id not in options:
                options[initial_id] = str(initial_value)
            option_ids = list(options.keys())
            selected_id = (
                initial_id
                if initial_id is not None and initial_id in options
                else (option_ids[0] if option_ids else None)
            )
            if not option_ids:
                st.caption("No matching records")
                return None
            return st.selectbox(
                label,
                options=option_ids,
                index=option_ids.index(selected_id) if selected_id in option_ids else 0,
                format_func=lambda item_id: f"{item_id} - {options[item_id]}",
                key=key,
            )
        return st.number_input(label, value=int(initial_value or 0), step=1, key=key)

    if field_type in {"Double", "Decimal"}:
        value = float(initial_value) if initial_value not in (None, "") else 0.0
        return Decimal(str(st.number_input(label, value=value, step=0.1, key=key)))

    if field_type == "Boolean":
        return st.checkbox(label, value=bool(initial_value), key=key)

    if field_type == "Text":
        return st.text_area(label, value=str(initial_value or ""), key=key)

    if field_type == "Date":
        parsed = None
        if isinstance(initial_value, str):
            try:
                parsed = date.fromisoformat(initial_value)
            except ValueError:
                parsed = None
        return st.date_input(label, value=parsed, key=key).isoformat() if parsed else st.date_input(label, key=key).isoformat()

    if field_type == "DateTime":
        default = datetime.now() if not initial_value else datetime.fromisoformat(str(initial_value))
        return st.datetime_input(label, value=default, key=key).isoformat()

    return st.text_input(label, value=str(initial_value or ""), key=key)

