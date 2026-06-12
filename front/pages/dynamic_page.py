from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from api.crud import delete_row, detail_row, insert_row, list_rows, update_row
from components.dynamic_form import render_dynamic_form
from components.dynamic_table import render_data_grid, render_export_button, render_toolbar
from components.filters import render_filter_controls, validate_filters
from components.notifications import show_api_error, show_success
from services.metadata import (
    load_foreign_key_labels_cached,
    load_form_schema_cached,
    load_lookup_values_cached,
)
from utils.models import ApiError


def render_dynamic_page(*, base_url: str, access_token: str, selected_menu: dict) -> None:
    form_info = selected_menu.get("form") or {}
    if not form_info:
        st.info("Select a leaf menu bound to a form.")
        return

    scope_key = str(selected_menu["id"])
    permissions = selected_menu.get("permissions", {})
    target = {"menu": selected_menu["name"]}

    st.title(selected_menu["name"])
    st.caption(f"Form: {form_info.get('name')} | Table: {form_info.get('table_name')}")

    try:
        form_schema = load_form_schema_cached(
            base_url,
            access_token,
            st.session_state.get("metadata_version", ""),
            form_info["table_name"],
        )
    except ApiError as exc:
        show_api_error(exc.message, exc.field)
        return

    fields = form_schema.get("fields", [])
    filters = render_filter_controls(fields, scope_key)

    valid, message = validate_filters(fields, filters)
    if not valid:
        st.warning(message)

    page_size = st.selectbox("Page size", options=[25, 50, 100, 250], index=1, key=f"page-size-{scope_key}")
    page_index = st.number_input("Page", min_value=1, value=1, step=1, key=f"page-{scope_key}")
    offset = int((page_index - 1) * page_size)

    actions = render_toolbar(
        can_insert=bool(permissions.get("can_insert")),
        can_delete=bool(permissions.get("can_delete")),
        can_print=bool(permissions.get("can_print")),
        count=st.session_state.get(f"count-{scope_key}", 0),
    )

    if actions["insert"]:
        st.session_state[f"open-insert-{scope_key}"] = True
    if actions["refresh"]:
        st.session_state[f"reload-{scope_key}"] = True

    if not valid:
        return

    try:
        with st.spinner("Loading data..."):
            listing = list_rows(
                base_url=base_url,
                access_token=access_token,
                payload={
                    **target,
                    "limit": page_size,
                    "offset": offset,
                    "sort_by": "id",
                    "sort_direction": "asc",
                    "filters": filters,
                },
            )
    except ApiError as exc:
        show_api_error(exc.message, exc.field)
        return

    items = listing.get("items", [])
    total_count = int(listing.get("count", 0))
    st.session_state[f"count-{scope_key}"] = total_count

    display_items = _enrich_rows_with_labels(
        base_url=base_url,
        access_token=access_token,
        fields=fields,
        items=items,
        metadata_version=st.session_state.get("metadata_version", ""),
    )
    df = pd.DataFrame(display_items)
    grid_result = render_data_grid(df, key=f"grid-{scope_key}")
    selected_rows = grid_result.get("selected_rows") if isinstance(grid_result, dict) else []
    double_clicked_row = _get_double_clicked_row(grid_result, scope_key=scope_key)
    if double_clicked_row:
        st.session_state[f"open-edit-{scope_key}"] = True
        st.session_state[f"edit-row-{scope_key}"] = double_clicked_row

    if actions["export"] and not df.empty:
        render_export_button(df, key=f"export-{scope_key}", filename=f"{form_info['table_name']}.csv")

    selected_row = _get_first_selected(selected_rows)
    if selected_row:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Edit selected", use_container_width=True, key=f"edit-btn-{scope_key}"):
                st.session_state[f"open-edit-{scope_key}"] = True
                st.session_state[f"edit-row-{scope_key}"] = selected_row
        with col2:
            if actions["delete"]:
                if st.button("Delete selected", use_container_width=True, key=f"delete-btn-{scope_key}"):
                    st.session_state[f"pending-delete-{scope_key}"] = int(selected_row["id"])
                    st.session_state[f"open-delete-confirm-{scope_key}"] = True

    if st.session_state.get(f"open-insert-{scope_key}"):
        _show_insert_dialog(
            base_url=base_url,
            access_token=access_token,
            target=target,
            form_name=form_info["table_name"],
            fields=fields,
            scope_key=scope_key,
            metadata_version=st.session_state.get("metadata_version", ""),
        )

    if st.session_state.get(f"open-edit-{scope_key}"):
        _show_edit_dialog(
            base_url=base_url,
            access_token=access_token,
            target=target,
            form_name=form_info["table_name"],
            fields=fields,
            scope_key=scope_key,
            metadata_version=st.session_state.get("metadata_version", ""),
        )

    if st.session_state.get(f"open-delete-confirm-{scope_key}"):
        _show_delete_confirmation_dialog(
            base_url=base_url,
            access_token=access_token,
            target=target,
            scope_key=scope_key,
        )


def _get_first_selected(selected_rows: Any) -> dict | None:
    if isinstance(selected_rows, list) and selected_rows:
        row = selected_rows[0]
        if isinstance(row, dict) and row.get("id"):
            return row
    return None


def _get_double_clicked_row(grid_result: Any, *, scope_key: str) -> dict | None:
    if not isinstance(grid_result, dict):
        return None
    data = grid_result.get("data")
    if data is None:
        return None

    if hasattr(data, "to_dict"):
        rows = data.to_dict(orient="records")
    elif isinstance(data, list):
        rows = data
    else:
        return None

    rows_with_marker = [row for row in rows if isinstance(row, dict) and int(row.get("__open_edit__", 0) or 0) > 0]
    if not rows_with_marker:
        return None

    row = max(rows_with_marker, key=lambda item: int(item.get("__open_edit__", 0) or 0))
    marker = int(row.get("__open_edit__", 0) or 0)
    marker_key = f"last-open-edit-ts-{scope_key}"
    if marker <= int(st.session_state.get(marker_key, 0)):
        return None
    st.session_state[marker_key] = marker

    if not row.get("id"):
        return None
    normalized = dict(row)
    normalized.pop("__open_edit__", None)
    return normalized


def _delete_selected(*, base_url: str, access_token: str, target: dict, record_id: int) -> None:
    try:
        delete_row(
            base_url=base_url,
            access_token=access_token,
            payload={**target, "data": {"id": int(record_id)}},
        )
        show_success("Record deleted")
    except ApiError as exc:
        show_api_error(exc.message, exc.field)


@st.dialog("Confirm deletion", width="small")
def _show_delete_confirmation_dialog(
    *,
    base_url: str,
    access_token: str,
    target: dict,
    scope_key: str,
) -> None:
    record_id = st.session_state.get(f"pending-delete-{scope_key}")
    if not record_id:
        st.session_state[f"open-delete-confirm-{scope_key}"] = False
        return

    st.warning(f"Are you sure you want to delete record #{record_id}? This action cannot be undone.")
    cancel_col, confirm_col = st.columns(2)
    with cancel_col:
        if st.button("Cancel", use_container_width=True, key=f"delete-cancel-{scope_key}"):
            st.session_state[f"open-delete-confirm-{scope_key}"] = False
            st.session_state.pop(f"pending-delete-{scope_key}", None)
            st.rerun()
    with confirm_col:
        if st.button("Delete", use_container_width=True, key=f"delete-confirm-{scope_key}"):
            _delete_selected(
                base_url=base_url,
                access_token=access_token,
                target=target,
                record_id=int(record_id),
            )
            st.session_state[f"open-delete-confirm-{scope_key}"] = False
            st.session_state.pop(f"pending-delete-{scope_key}", None)
            st.rerun()


def _enrich_rows_with_labels(
    *,
    base_url: str,
    access_token: str,
    fields: list[dict],
    items: list[dict],
    metadata_version: str,
) -> list[dict]:
    if not items:
        return items

    display_items = [dict(item) for item in items]
    for field in fields:
        field_name = field["name"]
        field_type = field["type"]

        if field_type == "Lookup" and field.get("lookup_id"):
            lookup_values = load_lookup_values_cached(
                base_url,
                access_token,
                metadata_version,
                int(field["lookup_id"]),
                query="",
                limit=2000,
            )
            lookup_map = {int(item["id"]): str(item["value"]) for item in lookup_values}
            for row in display_items:
                value = row.get(field_name)
                if isinstance(value, int):
                    row[field_name] = lookup_map.get(value, str(value))

        if field_type == "ForeignKey" and field.get("foreign_key_table"):
            ids = tuple(sorted({int(row[field_name]) for row in items if isinstance(row.get(field_name), int)}))
            labels = load_foreign_key_labels_cached(
                base_url,
                access_token,
                metadata_version,
                str(field["foreign_key_table"]),
                ids,
            )
            for row in display_items:
                value = row.get(field_name)
                if isinstance(value, int):
                    label = labels.get(value, str(value))
                    row[field_name] = f"{label} [{value}]"

    return display_items


@st.dialog("Insert Record", width="large")
def _show_insert_dialog(
    *,
    base_url: str,
    access_token: str,
    target: dict,
    form_name: str,
    fields: list[dict],
    scope_key: str,
    metadata_version: str,
) -> None:
    submitted, payload = render_dynamic_form(
        base_url=base_url,
        access_token=access_token,
        form_name=form_name,
        fields=fields,
        initial_data=None,
        scope_key=f"insert-{scope_key}",
        metadata_version=metadata_version,
    )
    if submitted:
        try:
            insert_row(base_url=base_url, access_token=access_token, payload={**target, "data": payload})
            st.session_state[f"open-insert-{scope_key}"] = False
            show_success("Record inserted")
            st.rerun()
        except ApiError as exc:
            show_api_error(exc.message, exc.field)


@st.dialog("Edit Record", width="large")
def _show_edit_dialog(
    *,
    base_url: str,
    access_token: str,
    target: dict,
    form_name: str,
    fields: list[dict],
    scope_key: str,
    metadata_version: str,
) -> None:
    row = st.session_state.get(f"edit-row-{scope_key}")
    if not row:
        st.warning("No row selected")
        return

    initial_data = detail_row(base_url=base_url, access_token=access_token, payload={**target, "id": int(row["id"])})

    submitted, payload = render_dynamic_form(
        base_url=base_url,
        access_token=access_token,
        form_name=form_name,
        fields=fields,
        initial_data=initial_data,
        scope_key=f"edit-{scope_key}",
        metadata_version=metadata_version,
    )
    if submitted:
        try:
            update_row(base_url=base_url, access_token=access_token, payload={**target, "data": payload})
            st.session_state[f"open-edit-{scope_key}"] = False
            show_success("Record updated")
            st.rerun()
        except ApiError as exc:
            show_api_error(exc.message, exc.field)

