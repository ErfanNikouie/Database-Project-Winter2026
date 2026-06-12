from __future__ import annotations

import streamlit as st

from api.auth import logout
from services.session import clear_auth


def render_sidebar(*, base_url: str, menu_tree: list[dict], access_token: str, refresh_token: str) -> tuple[str, dict | None]:
    selected_page = st.session_state.get("active_page", "home")
    selected_menu = None

    with st.sidebar:
        st.markdown("## HRMS")
        st.caption("Dynamic Enterprise Platform")

        if st.button("Profile", use_container_width=True):
            st.session_state.active_page = "profile"
            selected_page = "profile"

        st.markdown("### Navigation")
        for node in menu_tree:
            current = _render_menu_node(node)
            if selected_menu is None and current is not None:
                selected_menu = current

        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            try:
                if access_token and refresh_token:
                    logout(base_url=base_url, access_token=access_token, refresh_token=refresh_token)
            except Exception:
                # Clear local auth even if backend logout fails.
                pass
            clear_auth()
            st.rerun()

    return selected_page, selected_menu


def _render_menu_node(node: dict) -> dict | None:
    if node.get("children"):
        with st.expander(node["name"], expanded=False):
            selected = None
            for child in node["children"]:
                current = _render_menu_node(child)
                if selected is None and current is not None:
                    selected = current
            return selected

    form_info = node.get("form")
    if not form_info:
        st.caption(node["name"])
        return None

    is_active = st.session_state.get("selected_menu_id") == node["id"]
    if st.button(
        node["name"],
        key=f"menu-{node['id']}",
        use_container_width=True,
        type="primary" if is_active else "secondary",
    ):
        st.session_state.selected_menu_id = node["id"]
        st.session_state.active_page = "dynamic"
        st.session_state.selected_menu = node
        return node
    return None

