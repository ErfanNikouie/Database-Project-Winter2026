from __future__ import annotations

import re

import streamlit as st

from utils.filter_help import FILTER_HELP_BY_TYPE


_SIMPLE_NUMERIC_PATTERN = re.compile(r"^[0-9()\s<>=!&|.,+-]+$")


def render_filter_controls(fields: list[dict], scope_key: str) -> dict[str, str]:
    filters: dict[str, str] = {}
    with st.expander("Filters", expanded=False):
        for field in fields:
            name = field["name"]
            field_type = field["type"]
            label = f"{name} ({field_type})"
            if field_type == "Boolean":
                value = st.selectbox(
                    label,
                    options=["Don't Care", "True", "False"],
                    index=0,
                    key=f"filter-{scope_key}-{name}",
                )
                if value != "Don't Care":
                    filters[name] = value
            else:
                value = st.text_input(
                    label,
                    key=f"filter-{scope_key}-{name}",
                    placeholder=FILTER_HELP_BY_TYPE.get(field_type, ""),
                )
                if value.strip():
                    filters[name] = value.strip()

    return filters


def validate_filters(fields: list[dict], filters: dict[str, str]) -> tuple[bool, str | None]:
    field_type_map = {f["name"]: f["type"] for f in fields}
    for field_name, raw in filters.items():
        field_type = field_type_map.get(field_name)
        if not field_type:
            continue

        if field_type in {"Integer", "Double", "Decimal", "Date", "DateTime", "ForeignKey"}:
            if not _SIMPLE_NUMERIC_PATTERN.match(raw):
                return False, f"Invalid filter syntax for {field_name}"

        if field_type == "Boolean" and raw not in {"True", "False", "true", "false"}:
            return False, f"Boolean filter for {field_name} must be True or False"

    return True, None

