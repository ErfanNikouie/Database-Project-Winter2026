from __future__ import annotations

from io import StringIO
from typing import Any

import pandas as pd
from dash import ALL, Input, Output, State, callback, dcc, no_update

from components.dynamic_form import build_dynamic_form
from components.dynamic_table import build_empty_grid, build_grid, build_toolbar
from components.filters import build_filter_section
from services.api_client import api_client
from services.display_service import enrich_rows_for_display
from services.metadata_service import fetch_form_schema
from utils.models import ApiError


@callback(
    Output("schema-store", "data"),
    Output("dynamic-page-title", "children"),
    Output("dynamic-page-table", "children"),
    Output("dynamic-filter-section", "children"),
    Output("insert-form-container", "children"),
    Output("edit-form-container", "children"),
    Input("active-menu-id-hint", "data", allow_optional=True),
    State("ui-store", "data"),
    State("auth-store", "data"),
    prevent_initial_call=True,
)
def load_schema(active_menu_id: str | None, ui_store: dict, auth_data: dict):
    if not active_menu_id or not auth_data or not auth_data.get("authenticated"):
        return {}, "", "", "", no_update, no_update

    menu = _resolve_menu(ui_store, int(active_menu_id))
    if not menu or not menu.get("form"):
        return {}, "", "", "", no_update, no_update

    form = menu["form"]
    schema = fetch_form_schema(
        base_url=_base_url(),
        access_token=auth_data["access_token"],
        metadata_version=(ui_store or {}).get("metadata_version", ""),
        table_name=form["table_name"],
    )
    schema_payload = {**schema, "_table_name": form["table_name"]}
    fields = schema_payload.get("fields", [])
    fk_options_by_field = _build_fk_options(fields, auth_data["access_token"])
    lookup_options_by_field = _build_lookup_options(fields, auth_data["access_token"])
    return (
        schema_payload,
        menu["name"],
        form["table_name"],
        build_filter_section(
            fields=fields,
            fk_options_by_field=fk_options_by_field,
            lookup_options_by_field=lookup_options_by_field,
        ),
        build_dynamic_form(
            form_key="insert",
            fields=fields,
            fk_options_by_field=fk_options_by_field,
            lookup_options_by_field=lookup_options_by_field,
            mode="insert",
        ),
        build_dynamic_form(
            form_key="edit",
            fields=fields,
            fk_options_by_field=fk_options_by_field,
            lookup_options_by_field=lookup_options_by_field,
            mode="edit",
        ),
    )


@callback(
    Output("table-store", "data"),
    Output("dynamic-toolbar", "children"),
    Output("dynamic-grid-wrapper", "children"),
    Output("dynamic-page-error", "children"),
    Input({"type": "toolbar-action", "action": "refresh", "index": ALL}, "n_clicks"),
    Input("active-menu-id-hint", "data", allow_optional=True),
    Input("schema-store", "data"),
    Input("crud-action-local", "data", allow_optional=True),
    State("auth-store", "data"),
    State("ui-store", "data"),
    State({"type": "filter-field", "name": ALL}, "id"),
    State({"type": "filter-field", "name": ALL}, "value"),
    State({"type": "filter-date-bound", "name": ALL, "bound": ALL}, "id"),
    State({"type": "filter-date-bound", "name": ALL, "bound": ALL}, "value"),
    prevent_initial_call=True,
)
def load_rows(
    _refresh_clicks: list[int] | None,
    active_menu_id: str | None,
    schema: dict,
    _crud_action: dict | None,
    auth_data: dict,
    ui_store: dict,
    filter_ids: list[dict[str, Any]] | None,
    filter_values: list[Any] | None,
    filter_date_ids: list[dict[str, Any]] | None,
    filter_date_values: list[Any] | None,
):
    if not active_menu_id or not auth_data or not auth_data.get("authenticated"):
        return {"rows": [], "count": 0}, "", build_empty_grid(), ""

    menu = _resolve_menu(ui_store, int(active_menu_id))
    if not menu:
        return {"rows": [], "count": 0}, "", build_empty_grid(), "Unknown menu"

    form = menu.get("form") or {}
    if not form.get("name"):
        return {"rows": [], "count": 0}, "", build_empty_grid(), "Selected menu is not bound to a form"

    schema_table_name = (schema or {}).get("_table_name")
    if schema_table_name != form.get("table_name"):
        toolbar = build_toolbar(
            can_insert=bool((menu.get("permissions") or {}).get("can_insert")),
            can_delete=bool((menu.get("permissions") or {}).get("can_delete")),
            can_print=bool((menu.get("permissions") or {}).get("can_print")),
            count=0,
            menu_index=int(active_menu_id),
        )
        return {"rows": [], "count": 0}, toolbar, build_empty_grid(), ""

    target = {"form": form["name"]}
    permissions = menu.get("permissions", {})

    payload = {
        **target,
        "limit": 50,
        "offset": 0,
        "sort_by": "id",
        "sort_direction": "asc",
        "filters": _build_filters(filter_ids, filter_values, filter_date_ids, filter_date_values),
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
    display_rows, columns = enrich_rows_for_display(
        base_url=_base_url(),
        access_token=auth_data["access_token"],
        schema=schema,
        rows=rows,
    )
    toolbar = build_toolbar(
        can_insert=bool(permissions.get("can_insert")),
        can_delete=bool(permissions.get("can_delete")),
        can_print=bool(permissions.get("can_print")),
        count=int(listing.get("count", 0)),
        menu_index=int(active_menu_id),
    )
    grid = build_grid(rows=display_rows, columns=columns) if rows else build_empty_grid()
    return {"rows": display_rows, "count": int(listing.get("count", 0))}, toolbar, grid, ""


@callback(
    Output("insert-modal", "opened"),
    Output("insert-modal-error", "children"),
    Output("crud-action-local", "data", allow_duplicate=True),
    Output("crud-action-store", "data", allow_duplicate=True),
    Input({"type": "toolbar-action", "action": "insert", "index": ALL}, "n_clicks"),
    Input("insert-cancel", "n_clicks"),
    Input("insert-confirm", "n_clicks"),
    State({"type": "form-field-insert", "name": ALL}, "id"),
    State({"type": "form-field-insert", "name": ALL}, "value"),
    State("schema-store", "data"),
    State("table-store", "data"),
    State("active-menu-id-hint", "data", allow_optional=True),
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
        return no_update, no_update, no_update, no_update

    if isinstance(trigger, dict) and trigger.get("action") == "insert":
        if _max_clicks(insert_clicks) <= 0:
            return no_update, no_update, no_update, no_update
        return True, "", no_update, no_update

    if trigger == "insert-cancel":
        return False, "", no_update, no_update

    if trigger != "insert-confirm":
        return no_update, no_update, no_update, no_update

    if (confirm_clicks or 0) <= 0:
        return no_update, no_update, no_update, no_update

    if not active_menu_id or not auth_data or not auth_data.get("authenticated"):
        return True, "Unauthorized", no_update, no_update

    menu = _resolve_menu(ui_store, int(active_menu_id))
    form = (menu or {}).get("form") or {}
    form_name = form.get("name")
    if not form_name:
        return True, "Selected menu is not bound to a form", no_update, no_update

    payload_data = _build_typed_payload(insert_field_ids, insert_field_values, schema)

    validation_error = _validate_insert_payload(schema, payload_data, table_store)
    if validation_error:
        return True, validation_error, no_update, no_update

    try:
        api_client.insert_row(
            base_url=_base_url(),
            access_token=auth_data["access_token"],
            payload={"form": form_name, "data": payload_data},
        )
        event = {"ts": int(confirm_clicks or 0), "action": "insert", "menu_id": int(active_menu_id)}
        return False, "", event, event
    except ApiError as exc:
        return True, exc.message, no_update, no_update


@callback(
    Output({"type": "form-field-insert", "name": ALL}, "value"),
    Input("insert-modal", "opened"),
    State({"type": "form-field-insert", "name": ALL}, "id"),
    prevent_initial_call=True,
)
def clear_insert_form_values(opened: bool, field_ids: list[dict[str, Any]] | None):
    if not field_ids:
        return []
    if opened:
        return [no_update for _ in field_ids]

    cleared = []
    for field_id in field_ids:
        name = (field_id or {}).get("name")
        if name in {"id", "created_at", "updated_at", "password_hash"}:
            cleared.append("Auto generated")
        else:
            cleared.append(None)
    return cleared


@callback(
    Output("edit-modal", "opened"),
    Output("edit-modal-error", "children"),
    Output({"type": "form-field-edit", "name": ALL}, "value"),
    Output("edit-row-store", "data"),
    Output("crud-action-local", "data", allow_duplicate=True),
    Output("crud-action-store", "data", allow_duplicate=True),
    Input("dynamic-grid", "cellDoubleClicked"),
    Input("edit-cancel", "n_clicks"),
    Input("edit-confirm", "n_clicks"),
    State("dynamic-grid", "selectedRows"),
    State({"type": "form-field-edit", "name": ALL}, "id"),
    State({"type": "form-field-edit", "name": ALL}, "value"),
    State("active-menu-id-hint", "data", allow_optional=True),
    State("auth-store", "data"),
    State("ui-store", "data"),
    State("schema-store", "data"),
    prevent_initial_call=True,
)
def handle_edit_modal(
    cell_double_clicked: dict | None,
    cancel_clicks: int | None,
    confirm_clicks: int | None,
    selected_rows: list[dict[str, Any]] | None,
    edit_field_ids: list[dict[str, Any]] | None,
    edit_field_values: list[Any] | None,
    active_menu_id: str | None,
    auth_data: dict,
    ui_store: dict,
    schema: dict,
):
    from dash import callback_context

    trigger = callback_context.triggered_id
    if trigger == "dynamic-grid":
        if not cell_double_clicked:
            return no_update, no_update, [no_update for _ in (edit_field_ids or [])], no_update, no_update, no_update
        row = (cell_double_clicked or {}).get("data") or (selected_rows[0] if selected_rows else None)
        if not row:
            return no_update, no_update, [no_update for _ in (edit_field_ids or [])], no_update, no_update, no_update
        row_id = row.get("id")
        if row_id is None:
            return no_update, "Selected row has no id", [no_update for _ in (edit_field_ids or [])], no_update, no_update, no_update
        values = _map_row_to_form_values(row, edit_field_ids, schema)
        return True, "", values, {"id": row_id}, no_update, no_update

    if trigger == "edit-cancel":
        values = [no_update for _ in (edit_field_ids or [])]
        return False, "", values, {}, no_update, no_update

    if trigger != "edit-confirm":
        return no_update, no_update, [no_update for _ in (edit_field_ids or [])], no_update, no_update, no_update

    if not active_menu_id or not auth_data or not auth_data.get("authenticated"):
        return True, "Unauthorized", [no_update for _ in (edit_field_ids or [])], no_update, no_update, no_update

    row_id = (selected_rows or [{}])[0].get("id")
    if row_id is None:
        return True, "Select a row before saving", [no_update for _ in (edit_field_ids or [])], no_update, no_update, no_update

    menu = _resolve_menu(ui_store, int(active_menu_id))
    form_name = ((menu or {}).get("form") or {}).get("name")
    if not form_name:
        return True, "Selected menu is not bound to a form", [no_update for _ in (edit_field_ids or [])], no_update, no_update, no_update

    payload = _build_typed_payload(edit_field_ids, edit_field_values, schema)
    payload["id"] = int(row_id)

    try:
        api_client.update_row(
            base_url=_base_url(),
            access_token=auth_data["access_token"],
            payload={"form": form_name, "data": payload},
        )
        values = _clear_form_values(edit_field_ids)
        event = {"ts": int(confirm_clicks or 0), "action": "edit", "menu_id": int(active_menu_id)}
        return False, "", values, {}, event, event
    except ApiError as exc:
        return True, exc.message, [no_update for _ in (edit_field_ids or [])], no_update, no_update, no_update


@callback(
    Output("crud-action-local", "data", allow_duplicate=True),
    Output("crud-action-store", "data", allow_duplicate=True),
    Output("dynamic-page-error", "children", allow_duplicate=True),
    Input({"type": "toolbar-action", "action": "delete", "index": ALL}, "n_clicks"),
    State("dynamic-grid", "selectedRows"),
    State("active-menu-id-hint", "data", allow_optional=True),
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
        return no_update, no_update, no_update
    if not selected_rows:
        return no_update, no_update, "Select a row to delete"
    if not active_menu_id or not auth_data or not auth_data.get("authenticated"):
        return no_update, no_update, "Unauthorized"

    row_id = selected_rows[0].get("id")
    if row_id is None:
        return no_update, no_update, "Selected row is missing id"

    menu = _resolve_menu(ui_store, int(active_menu_id))
    form = (menu or {}).get("form") or {}
    form_name = form.get("name")
    if not form_name:
        return no_update, no_update, "Selected menu is not bound to a form"

    try:
        api_client.delete_row(
            base_url=_base_url(),
            access_token=auth_data["access_token"],
            payload={"form": form_name, "data": {"id": int(row_id)}},
        )
    except ApiError as exc:
        return no_update, no_update, exc.message

    ts = _max_clicks(delete_clicks)
    event = {"ts": int(ts), "action": "delete", "menu_id": int(active_menu_id)}
    return event, event, ""


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


def _build_filters(
    filter_ids: list[dict[str, Any]] | None,
    filter_values: list[Any] | None,
    filter_date_ids: list[dict[str, Any]] | None,
    filter_date_values: list[Any] | None,
) -> dict[str, Any]:
    filters: dict[str, Any] = {}
    for field_id, value in zip(filter_ids or [], filter_values or []):
        if not isinstance(field_id, dict):
            continue
        name = field_id.get("name")
        if not name or value in (None, ""):
            continue
        filters[str(name)] = value

    date_bounds: dict[str, dict[str, Any]] = {}
    for field_id, value in zip(filter_date_ids or [], filter_date_values or []):
        if not isinstance(field_id, dict):
            continue
        name = field_id.get("name")
        bound = field_id.get("bound")
        if not name or bound not in {"from", "to"} or value in (None, ""):
            continue
        entry = date_bounds.setdefault(str(name), {})
        entry[str(bound)] = value

    for name, bounds in date_bounds.items():
        range_tokens: list[str] = []
        if "from" in bounds:
            range_tokens.append(f">={_to_filter_literal(bounds['from'])}")
        if "to" in bounds:
            range_tokens.append(f"<={_to_filter_literal(bounds['to'])}")
        if range_tokens:
            filters[name] = "&".join(range_tokens)

    return filters


def _to_filter_literal(value: Any) -> str:
    text = str(value)
    if " " in text and "T" not in text:
        return text.replace(" ", "T")
    return text


def _max_clicks(clicks: list[int] | None) -> int:
    if not clicks:
        return 0
    return max((click or 0) for click in clicks)


def _build_insert_payload(field_ids: list[dict[str, Any]] | None, field_values: list[Any] | None) -> dict[str, Any]:
    return _build_typed_payload(field_ids, field_values, None)


def _build_typed_payload(
    field_ids: list[dict[str, Any]] | None,
    field_values: list[Any] | None,
    schema: dict | None,
) -> dict[str, Any]:
    if not field_ids or not field_values:
        return {}

    field_types = {field.get("name"): field.get("type") for field in (schema or {}).get("fields", [])}
    payload: dict[str, Any] = {}
    for field_id, value in zip(field_ids, field_values):
        if not isinstance(field_id, dict):
            continue
        name = field_id.get("name")
        if not name or name in {"id", "created_at", "updated_at", "password_hash"}:
            continue
        if value in (None, ""):
            continue

        field_type = field_types.get(name)
        if field_type in {"Integer", "Lookup", "ForeignKey"}:
            payload[str(name)] = int(value)
        elif field_type in {"Double", "Decimal"}:
            payload[str(name)] = float(value)
        elif field_type == "Boolean":
            payload[str(name)] = str(value).lower() == "true"
        else:
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


def _build_fk_options(fields: list[dict[str, Any]], access_token: str) -> dict[str, list[dict[str, str]]]:
    options: dict[str, list[dict[str, str]]] = {}
    for field in fields:
        if field.get("type") != "ForeignKey" or not field.get("foreign_key_table"):
            continue
        name = field.get("name")
        if not name:
            continue
        rows = api_client.list_options(
            base_url=_base_url(),
            access_token=access_token,
            payload={"table": field["foreign_key_table"], "limit": 200, "query": ""},
        )
        options[name] = [{"value": str(row["id"]), "label": str(row["label"])} for row in rows]
    return options


def _build_lookup_options(fields: list[dict[str, Any]], access_token: str) -> dict[str, list[dict[str, str]]]:
    options: dict[str, list[dict[str, str]]] = {}
    for field in fields:
        if field.get("type") != "Lookup" or not field.get("lookup_id"):
            continue
        name = field.get("name")
        if not name:
            continue
        rows = api_client.list_rows(
            base_url=_base_url(),
            access_token=access_token,
            payload={
                "form": "LookupValue",
                "limit": 1000,
                "offset": 0,
                "sort_by": "value",
                "sort_direction": "asc",
                "filters": {"lookup_id": int(field["lookup_id"])},
            },
        ).get("items", [])
        options[name] = [{"value": str(row["id"]), "label": str(row.get("value", row["id"]))} for row in rows]
    return options


def _map_row_to_form_values(
    row: dict[str, Any],
    field_ids: list[dict[str, Any]] | None,
    schema: dict[str, Any] | None,
) -> list[Any]:
    if not field_ids:
        return []
    field_types = {field.get("name"): field.get("type") for field in (schema or {}).get("fields", [])}
    values: list[Any] = []
    for field_id in field_ids:
        name = (field_id or {}).get("name")
        if not name:
            values.append(None)
            continue
        value = row.get(name)
        field_type = field_types.get(name)
        if field_type in {"ForeignKey", "Lookup"}:
            values.append(None if value in (None, "") else str(value))
            continue
        if field_type == "Boolean":
            values.append("" if value in (None, "") else str(value))
            continue
        values.append(value)
    return values


def _clear_form_values(field_ids: list[dict[str, Any]] | None) -> list[Any]:
    if not field_ids:
        return []
    cleared = []
    for field_id in field_ids:
        name = (field_id or {}).get("name")
        if name in {"id", "created_at", "updated_at", "password_hash"}:
            cleared.append("Auto generated")
        else:
            cleared.append(None)
    return cleared


