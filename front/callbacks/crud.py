from __future__ import annotations

from dash import ALL, Input, Output, State, callback, no_update

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
    Input("active-menu-id", "data"),
    State("ui-store", "data"),
    State("auth-store", "data"),
    prevent_initial_call=False,
)
def load_schema(active_menu_id: str | None, ui_store: dict, auth_data: dict):
    if not active_menu_id or not auth_data or not auth_data.get("authenticated"):
        return {}, "", "", ""

    menu = _resolve_menu(ui_store, int(active_menu_id))
    if not menu or not menu.get("form"):
        return {}, "", "", ""

    form = menu["form"]
    schema = fetch_form_schema(
        base_url=_base_url(),
        access_token=auth_data["access_token"],
        metadata_version=(ui_store or {}).get("metadata_version", ""),
        table_name=form["table_name"],
    )
    fields = schema.get("fields", [])
    return schema, menu["name"], form["table_name"], build_filter_section(fields=fields)


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
    prevent_initial_call=False,
)
def load_rows(_refresh_clicks: list[int] | None, active_menu_id: str | None, auth_data: dict, ui_store: dict, schema: dict):
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
        "filters": {},
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
    )
    grid = build_grid(rows=rows, columns=columns) if rows else build_empty_grid()
    return {"rows": rows, "count": int(listing.get("count", 0))}, toolbar, grid, ""


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


# ...existing code...


