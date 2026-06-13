from __future__ import annotations

from dash import ALL, Input, Output, State, callback, callback_context, no_update

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
    auth_user = (auth_data or {}).get("user") or {}
    auth_user_id = auth_user.get("id")
    if ui.get("auth_user_id") != auth_user_id:
        ui["menu_tree"] = []
        ui["menu_tree_etag"] = None
        ui["expanded_menu_folders"] = []
        ui["selected_menu_id"] = None
    ui["auth_user_id"] = auth_user_id
    selected_menu_id = _extract_menu_id(pathname)
    if selected_menu_id is not None:
        ui["selected_menu_id"] = selected_menu_id
    else:
        ui["selected_menu_id"] = None

    expanded_folder_ids = [int(item) for item in (ui.get("expanded_menu_folders") or []) if str(item).isdigit()]

    trigger = callback_context.triggered_id
    cached_items = ui.get("menu_tree") or []
    if trigger == "_pages_location" and cached_items:
        if selected_menu_id is not None:
            expanded_folder_ids = sorted(set(expanded_folder_ids) | _ancestor_folder_ids(cached_items, selected_menu_id))
        ui["expanded_menu_folders"] = expanded_folder_ids
        return ui, build_sidebar(cached_items, ui.get("selected_menu_id"), ui.get("expanded_menu_folders"))

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
            cache_scope=str(auth_user_id or "anon"),
        )
        ui["menu_tree"] = items
        ui["menu_tree_etag"] = next_etag
        if selected_menu_id is not None:
            expanded_folder_ids = sorted(set(expanded_folder_ids) | _ancestor_folder_ids(items, selected_menu_id))
            ui["expanded_menu_folders"] = expanded_folder_ids
    except ApiError:
        items = ui.get("menu_tree", [])

    return ui, build_sidebar(items, ui.get("selected_menu_id"), ui.get("expanded_menu_folders"))


@callback(
    Output("ui-store", "data", allow_duplicate=True),
    Input({"type": "menu-folder", "folder_id": ALL}, "value"),
    State({"type": "menu-folder", "folder_id": ALL}, "id"),
    State("ui-store", "data"),
    prevent_initial_call=True,
)
def track_expanded_menu_folders(values: list[str | None], folder_ids: list[dict], ui_store: dict):
    if not folder_ids:
        return no_update

    expanded: list[int] = []
    for value, folder_id in zip(values or [], folder_ids):
        if value and isinstance(folder_id, dict) and folder_id.get("folder_id") is not None:
            expanded.append(int(folder_id["folder_id"]))

    ui = dict(ui_store or {})
    ui["expanded_menu_folders"] = sorted(set(expanded))
    return ui


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


def _ancestor_folder_ids(menu_tree: list[dict], selected_menu_id: int) -> set[int]:
    ancestors: set[int] = set()

    def walk(nodes: list[dict], path: list[int]) -> bool:
        for node in nodes:
            node_id = node.get("id")
            children = node.get("children") or []

            if node_id == selected_menu_id:
                ancestors.update(path)
                return True

            if children and walk(children, [*path, int(node_id)]):
                return True
        return False

    walk(menu_tree or [], [])
    return ancestors



