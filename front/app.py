from __future__ import annotations

import time

import streamlit as st

from api.auth import get_current_user, refresh_access_token
from api.base import DEFAULT_BASE_URL
from api.menus import get_menu_tree
from components.notifications import show_api_error
from components.sidebar import render_sidebar
from pages.dynamic_page import render_dynamic_page
from pages.login import render_login_page
from pages.profile import render_profile_page
from services.metadata import clear_metadata_cache, refresh_metadata_version
from services.session import init_session_state, is_authenticated
from styles.css import inject_css
from utils.models import ApiError


st.set_page_config(page_title="HRMS", page_icon="🧭", layout="wide")


def main() -> None:
    init_session_state()
    inject_css()

    base_url = DEFAULT_BASE_URL

    if not is_authenticated():
        render_login_page(base_url=base_url)
        return

    try:
        if not st.session_state.get("current_user"):
            st.session_state.current_user = get_current_user(
                base_url=base_url,
                access_token=st.session_state.access_token,
            )
    except ApiError as exc:
        if exc.status_code == 401 and st.session_state.get("refresh_token"):
            _refresh_session(base_url)
        else:
            show_api_error(exc.message, exc.field)
            st.stop()

    _refresh_metadata_cache_state(base_url)

    menu_tree = _load_menu_tree(base_url)
    st.session_state.menu_tree = menu_tree

    _, selected_menu = render_sidebar(
        base_url=base_url,
        menu_tree=menu_tree,
        access_token=st.session_state.access_token,
        refresh_token=st.session_state.refresh_token,
    )

    active_page = st.session_state.get("active_page", "home")

    if active_page == "profile":
        render_profile_page(base_url=base_url, access_token=st.session_state.access_token)
        return

    if selected_menu:
        st.session_state.selected_menu = selected_menu

    menu = st.session_state.get("selected_menu")
    if menu:
        render_dynamic_page(base_url=base_url, access_token=st.session_state.access_token, selected_menu=menu)
        return

    st.markdown("""
    <div class="home-hero">
      <h1>HRMS Dynamic Platform</h1>
      <p>Use the menu on the left to open any form-driven page. Everything here is metadata-driven and permission-aware.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
            <div class="home-card">
              <h3>Navigation</h3>
              <p>Expand the sidebar tree and click a leaf menu item to load records.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """
            <div class="home-card">
              <h3>Data Operations</h3>
              <p>Use filters, insert, edit, delete, and export from each dynamic page.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _load_menu_tree(base_url: str) -> list[dict]:
    cache_key = "menu-tree-cache"
    current_etag = st.session_state.get("menu_tree_etag")

    try:
        with st.spinner("Loading menu tree..."):
            tree, next_etag = get_menu_tree(
                base_url=base_url,
                access_token=st.session_state.access_token,
                etag=current_etag,
            )
            if tree is None:
                return st.session_state.get(cache_key, [])
            st.session_state[cache_key] = tree
            st.session_state.menu_tree_etag = next_etag
            return tree
    except ApiError as exc:
        show_api_error(exc.message, exc.field)
        return []


def _refresh_metadata_cache_state(base_url: str) -> None:
    now = time.time()
    # Avoid metadata polling on every rerun.
    if now - float(st.session_state.get("metadata_checked_at", 0.0)) < 45:
        return

    try:
        new_version = refresh_metadata_version(
            base_url=base_url,
            access_token=st.session_state.access_token,
        )
    except ApiError:
        st.session_state.metadata_checked_at = now
        return

    old_version = st.session_state.get("metadata_version", "")
    if old_version and old_version != new_version:
        clear_metadata_cache()
        st.session_state["menu-tree-cache"] = []
        st.session_state.menu_tree_etag = None

    st.session_state.metadata_version = new_version
    st.session_state.metadata_checked_at = now


def _refresh_session(base_url: str) -> None:
    try:
        new_access = refresh_access_token(base_url=base_url, refresh_token=st.session_state.refresh_token)
        st.session_state.access_token = new_access
    except ApiError as exc:
        show_api_error(exc.message, exc.field)
        st.session_state.access_token = None
        st.session_state.refresh_token = None


if __name__ == "__main__":
    main()

