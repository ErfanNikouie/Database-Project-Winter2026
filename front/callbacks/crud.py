from __future__ import annotations

from io import StringIO
from typing import Any

import pandas as pd
from dash import ALL, Input, Output, State, callback, dcc, no_update

from components.dynamic_form import build_dynamic_form
from components.dynamic_table import build_empty_grid, build_grid, build_toolbar
from components.filters import build_filter_section
from services.api_client import api_client
from services.metadata_service import fetch_form_schema
from utils.models import ApiError


@callback(
    Output("schema-store", "data"),
    Output("dynamic-page-title", "children"),
    Output("dynamic-page-table", "children"),
    Output("dynamic-filter-section", "children"),
    Output("insert-form-container", "children"),
    Input("active-menu-id", "data"),
    State("ui-store", "data"),
    State("auth-store", "data"),
    prevent_initial_call=True,
)
def load_schema(active_menu_id: str | None, ui_store: dict, auth_data: dict):
    if not active_menu_id or not auth_data or not auth_data.get("authenticated"):
        return {}, "", "", "", no_update

    menu = _resolve_menu(ui_store, int(active_menu_id))
    if not menu or not menu.get("form"):
        return {}, "", "", "", no_update

    form = menu["form"]
    schema = fetch_form_schema(
        base_url=_base_url(),
        access_token=auth_data["access_token"],
        metadata_version=(ui_store or {}).get("metadata_version", ""),
        table_name=form["table_name"],
    )
    fields = schema.get("fields", [])
    return (
        schema,
        menu["name"],
        form["table_name"],
        build_filter_section(fields=fields),
        build_dynamic_form(form_key="insert", fields=fields),
    )


@callback(
    Output("table-store", "data"),
    Output("dynamic-toolbar", "children"),
    Output("dynamic-grid-wrapper", "children"),
    Output("dynamic-page-error", "children"),
    Input({"type": "toolbar-action", "action": "refresh", "index": ALL}, "n_clicks"),
    Input("active-menu-id", "data"),
    State("auth-store", "data"),
    State("ui-store", "data"),
    State("schema-store", "data"),
    State({"type": "filter-field", "name": ALL}, "id"),
    State({"type": "filter-field", "name": ALL}, "value"),
    prevent_initial_call=True,
)
def load_rows(
    _refresh_clicks: list[int] | None,
    active_menu_id: str | None,
    auth_data: dict,
    ui_store: dict,
    schema: dict,
    filter_ids: list[dict[str, Any]] | None,
    filter_values: list[Any] | None,
):
    if not active_menu_id or not auth_data or not auth_data.get("authenticated"):
        return {"rows": [], "count": 0}, "", build_empty_grid(), ""

    menu = _resolve_menu(ui_store, int(active_menu_id))
    if not menu:
        return {"rows": [], "count": 0}, "", build_empty_grid(), "Unknown menu"

    form = menu.get("form") or {}
    if not form.get("name"):
        return {"rows": [], "count": 0}, "", build_empty_grid(), "Selected menu is not bound to a form"
    target = {"form": form["name"]}
    permissions = menu.get("permissions", {})

    payload = {
        **target,
        "limit": 50,
        "offset": 0,
        "sort_by": "id",
        "sort_direction": "asc",
        "filters": _build_filters(filter_ids, filter_values),
    }

    try:
        listing = api_client.list_rows(
            base_url=_base_url(),
            access_token=auth_data["access_token"],
            payload=payload,
        )
    except ApiError as exc:
        return {"rows": [], "count": 0}, "", build_empty_grid(), exc.message

    rows = listing.get("items", [])
    columns = list(rows[0].keys()) if rows else [field["name"] for field in schema.get("fields", []) if field["name"] != "password_hash"]
    toolbar = build_toolbar(
        can_insert=bool(permissions.get("can_insert")),
        can_delete=bool(permissions.get("can_delete")),
        can_print=bool(permissions.get("can_print")),
        count=int(listing.get("count", 0)),
        menu_index=int(active_menu_id),
    )
    grid = build_grid(rows=rows, columns=columns) if rows else build_empty_grid()
    return {"rows": rows, "count": int(listing.get("count", 0))}, toolbar, grid, ""


@callback(
    Output("insert-modal", "opened"),
    Output("insert-modal-error", "children"),
    Input({"type": "toolbar-action", "action": "insert", "index": ALL}, "n_clicks"),
    Input("insert-cancel", "n_clicks"),
    Input("insert-confirm", "n_clicks"),
    State({"type": "form-field-insert", "name": ALL}, "id"),
    State({"type": "form-field-insert", "name": ALL}, "value"),
    State("schema-store", "data"),
    State("table-store", "data"),
    State("active-menu-id", "data"),
    State("auth-store", "data"),
    State("ui-store", "data"),
    prevent_initial_call=True,
)
def handle_insert_modal(
    insert_clicks: list[int] | None,
    cancel_clicks: int | None,
    confirm_clicks: int | None,
    insert_field_ids: list[dict[str, Any]] | None,
    insert_field_values: list[Any] | None,
    schema: dict,
    table_store: dict,
    active_menu_id: str | None,
    auth_data: dict,
    ui_store: dict,
):
    from dash import callback_context

    trigger = callback_context.triggered_id
    if trigger is None:
        return no_update, no_update

    if isinstance(trigger, dict) and trigger.get("action") == "insert":
        if _max_clicks(insert_clicks) <= 0:
            return no_update, no_update
        return True, ""

    if trigger == "insert-cancel":
        return False, ""

    if trigger != "insert-confirm":
        return no_update, no_update

    if (confirm_clicks or 0) <= 0:
        return no_update, no_update

    if not active_menu_id or not auth_data or not auth_data.get("authenticated"):
        return True, "Unauthorized"

    menu = _resolve_menu(ui_store, int(active_menu_id))
    form = (menu or {}).get("form") or {}
    form_name = form.get("name")
    if not form_name:
        return True, "Selected menu is not bound to a form"

    payload_data = _build_insert_payload(insert_field_ids, insert_field_values)

    validation_error = _validate_insert_payload(schema, payload_data, table_store)
    if validation_error:
        return True, validation_error

    try:
        api_client.insert_row(
            base_url=_base_url(),
            access_token=auth_data["access_token"],
            payload={"form": form_name, "data": payload_data},
        )
        return False, ""
    except ApiError as exc:
        return True, exc.message


@callback(
    Output({"type": "form-field-insert", "name": ALL}, "value"),
    Input("insert-modal", "opened"),
    State({"type": "form-field-insert", "name": ALL}, "id"),
    prevent_initial_call=True,
)
def clear_insert_form_values(opened: bool, field_ids: list[dict[str, Any]] | None):
    if opened:
        return no_update
    if not field_ids:
        return no_update

    cleared = []
    for field_id in field_ids:
        name = (field_id or {}).get("name")
        if name in {"id", "created_at", "updated_at", "password_hash"}:
            cleared.append("Auto generated")
        else:
            cleared.append(None)
    return cleared


@callback(
    Output("active-menu-id", "data", allow_duplicate=True),
    Output("dynamic-page-error", "children", allow_duplicate=True),
    Input("insert-confirm", "n_clicks"),
    State("insert-modal", "opened"),
    State("active-menu-id", "data"),
    prevent_initial_call=True,
)
def mark_insert_refresh(confirm_clicks: int | None, modal_opened: bool, active_menu_id: int | None):
    if not confirm_clicks or modal_opened or not active_menu_id:
        return no_update, no_update
    return active_menu_id, ""


@callback(
    Output("active-menu-id", "data", allow_duplicate=True),
    Output("dynamic-page-error", "children", allow_duplicate=True),
    Input({"type": "toolbar-action", "action": "delete", "index": ALL}, "n_clicks"),
    State("dynamic-grid", "selectedRows"),
    State("active-menu-id", "data"),
    State("auth-store", "data"),
    State("ui-store", "data"),
    prevent_initial_call=True,
)
def handle_delete(
    delete_clicks: list[int] | None,
    selected_rows: list[dict[str, Any]] | None,
    active_menu_id: str | None,
    auth_data: dict,
    ui_store: dict,
):
    if _max_clicks(delete_clicks) <= 0:
        return no_update, no_update
    if not selected_rows:
        return no_update, "Select a row to delete"
    if not active_menu_id or not auth_data or not auth_data.get("authenticated"):
        return no_update, "Unauthorized"

    row_id = selected_rows[0].get("id")
    if row_id is None:
        return no_update, "Selected row is missing id"

    menu = _resolve_menu(ui_store, int(active_menu_id))
    form = (menu or {}).get("form") or {}
    form_name = form.get("name")
    if not form_name:
        return no_update, "Selected menu is not bound to a form"

    try:
        api_client.delete_row(
            base_url=_base_url(),
            access_token=auth_data["access_token"],
            payload={"form": form_name, "data": {"id": int(row_id)}},
        )
    except ApiError as exc:
        return no_update, exc.message

    return int(active_menu_id), ""


@callback(
    Output("download-csv", "data"),
    Input({"type": "toolbar-action", "action": "export", "index": ALL}, "n_clicks"),
    State("table-store", "data"),
    prevent_initial_call=True,
)
def export_csv(export_clicks: list[int] | None, table_store: dict):
    if _max_clicks(export_clicks) <= 0:
        return no_update
    rows = (table_store or {}).get("rows") or []
    if not rows:
        return no_update
    df = pd.DataFrame(rows)
    return dcc.send_data_frame(df.to_csv, "export.csv", index=False)


def _resolve_menu(ui_store: dict | None, menu_id: int) -> dict | None:
    tree = (ui_store or {}).get("menu_tree") or []

    def walk(nodes: list[dict]):
        for node in nodes:
            if node.get("id") == menu_id:
                return node
            nested = node.get("children") or []
            found = walk(nested)
            if found:
                return found
        return None

    return walk(tree)


def _base_url() -> str:
    from api.base import DEFAULT_BASE_URL

    return DEFAULT_BASE_URL


def _build_filters(filter_ids: list[dict[str, Any]] | None, filter_values: list[Any] | None) -> dict[str, Any]:
    if not filter_ids or not filter_values:
        return {}
    filters: dict[str, Any] = {}
    for field_id, value in zip(filter_ids, filter_values):
        if not isinstance(field_id, dict):
            continue
        name = field_id.get("name")
        if not name:
            continue
        if value in (None, ""):
            continue
        filters[str(name)] = value
    return filters


def _max_clicks(clicks: list[int] | None) -> int:
    if not clicks:
        return 0
    return max((click or 0) for click in clicks)


def _build_insert_payload(field_ids: list[dict[str, Any]] | None, field_values: list[Any] | None) -> dict[str, Any]:
    if not field_ids or not field_values:
        return {}
    payload: dict[str, Any] = {}
    for field_id, value in zip(field_ids, field_values):
        if not isinstance(field_id, dict):
            continue
        name = field_id.get("name")
        if not name or name in {"id", "created_at", "updated_at", "password_hash"}:
            continue
        if value in (None, ""):
            continue
        payload[str(name)] = value
    return payload


def _validate_insert_payload(schema: dict | None, payload: dict[str, Any], table_store: dict | None) -> str | None:
    fields = (schema or {}).get("fields", [])
    if not fields:
        return None

    required_missing = []
    for field in fields:
        name = field.get("name")
        if not name or name in {"id", "created_at", "updated_at", "password_hash"}:
            continue
        if field.get("required") and name not in payload:
            required_missing.append(name)

    if required_missing:
        return f"Missing required fields: {', '.join(required_missing)}"

    # Lightweight uniqueness pre-check on currently loaded rows; backend stays authoritative.
    rows = (table_store or {}).get("rows") or []
    for field in fields:
        name = field.get("name")
        if not name or not field.get("unique"):
            continue
        if name not in payload:
            continue
        if any(str(row.get(name)) == str(payload[name]) for row in rows):
            return f"Field '{name}' must be unique"

    return None


