from __future__ import annotations

from dash import Input, Output, State, callback

from layouts.sidebar import build_sidebar
from services.metadata_service import fetch_metadata_version
from services.menu_service import fetch_menu_tree
from utils.models import ApiError


@callback(
    Output("ui-store", "data"),
    Output("sidebar-wrapper", "children"),
    Input("auth-store", "data"),
    Input("_pages_location", "pathname"),
    Input("crud-action-store", "data"),
    State("ui-store", "data"),
    prevent_initial_call=False,
)
def load_menus(auth_data: dict, pathname: str, crud_event: dict | None, ui_store: dict):
    if not auth_data or not auth_data.get("authenticated"):
        return ui_store, []

    ui = dict(ui_store or {})
    selected_menu_id = _extract_menu_id(pathname)
    if selected_menu_id:
        ui["selected_menu_id"] = selected_menu_id

    etag = ui.get("menu_tree_etag")
    if isinstance(crud_event, dict) and crud_event.get("action") in {"insert", "edit", "delete"}:
        etag = None
    try:
        ui["metadata_version"] = fetch_metadata_version(
            base_url=_base_url(),
            access_token=auth_data["access_token"],
        )
        items, next_etag = fetch_menu_tree(
            base_url=_base_url(),
            access_token=auth_data["access_token"],
            etag=etag,
        )
        ui["menu_tree"] = items
        ui["menu_tree_etag"] = next_etag
    except ApiError:
        items = ui.get("menu_tree", [])

    return ui, build_sidebar(items, ui.get("selected_menu_id"))


def _extract_menu_id(pathname: str | None) -> int | None:
    if not pathname or not pathname.startswith("/menu/"):
        return None
    try:
        return int(pathname.rsplit("/", maxsplit=1)[-1])
    except ValueError:
        return None


def _base_url() -> str:
    from api.base import DEFAULT_BASE_URL

    return DEFAULT_BASE_URL



