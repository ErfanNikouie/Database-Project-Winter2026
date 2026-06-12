from __future__ import annotations

from services.auth_service import empty_auth_payload


def default_auth_store() -> dict:
    return empty_auth_payload()


def default_ui_store() -> dict:
    return {
        "selected_menu_id": None,
        "selected_menu": None,
        "expanded_menu_folders": [],
        "menu_tree": [],
        "menu_tree_etag": None,
        "metadata_version": "",
        "notifications": [],
    }


