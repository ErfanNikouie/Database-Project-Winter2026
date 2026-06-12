from __future__ import annotations

import streamlit as st


DEFAULT_SESSION = {
    "access_token": None,
    "refresh_token": None,
    "current_user": None,
    "selected_menu_id": None,
    "active_page": "login",
    "menu_tree": [],
    "menu_tree_etag": None,
    "metadata_version": "",
    "metadata_checked_at": 0.0,
}


def init_session_state() -> None:
    for key, value in DEFAULT_SESSION.items():
        if key not in st.session_state:
            st.session_state[key] = value


def is_authenticated() -> bool:
    return bool(st.session_state.get("access_token"))


def set_auth(access_token: str, refresh_token: str, user_payload: dict) -> None:
    st.session_state.access_token = access_token
    st.session_state.refresh_token = refresh_token
    st.session_state.current_user = user_payload
    st.session_state.active_page = "home"
    st.session_state.menu_tree = []
    st.session_state.menu_tree_etag = None
    st.session_state.metadata_version = ""
    st.session_state.metadata_checked_at = 0.0


def clear_auth() -> None:
    for key in (
        "access_token",
        "refresh_token",
        "current_user",
        "selected_menu_id",
        "menu_tree",
        "menu_tree_etag",
        "metadata_version",
        "metadata_checked_at",
    ):
        st.session_state[key] = DEFAULT_SESSION[key]
    st.session_state.active_page = "login"

