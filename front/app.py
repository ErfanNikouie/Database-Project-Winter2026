from __future__ import annotations

import streamlit as st

from db.init_db import init_db
from services.initialization_service import initialize_default_hr_configuration
from services.menu_service import MenuService
from ui.sidebar import render_sidebar
from ui.pages.dynamic_form_page import render_dynamic_form
from ui.pages.form_management import render_form_management
from ui.pages.home import render_home
from ui.pages.lookup_management import render_lookup_management
from ui.pages.menu_management import render_menu_management
from ui.pages.user_management import render_user_management


st.set_page_config(page_title="Dynamic HR", layout="wide")


@st.cache_resource
def _init_once() -> None:

    init_db()


@st.cache_data(ttl=5)
def _get_menu_tree():

    return MenuService().build_tree()


def main() -> None:

    _init_once()

    if "active_menu_id" not in st.session_state:
        st.session_state.active_menu_id = None

    def on_menu_selected(menu_id: int) -> None:
        st.session_state.active_menu_id = int(menu_id)

    def on_initialize() -> None:
        try:
            initialize_default_hr_configuration()
            # invalidate cached menu tree
            st.cache_data.clear()
            st.success("Initialization completed")
            st.rerun()
        except Exception as e:
            st.error(f"Initialization failed: {e}")

    menu_tree = _get_menu_tree()
    render_sidebar(menu_tree, on_menu_selected=on_menu_selected, on_initialize=on_initialize)

    active_menu_id = st.session_state.active_menu_id
    if active_menu_id is None:
        render_home()
        return

    # Help type-checkers (Streamlit session_state is dynamically typed).
    assert active_menu_id is not None

    menu = MenuService().get_menu(int(active_menu_id))
    if menu is None:
        st.session_state.active_menu_id = None
        st.warning("Selected menu no longer exists")
        render_home()
        return

    # Route
    if menu.FormId is not None:
        render_dynamic_form(int(menu.FormId))
        return

    # Built-in management pages (leaf menus without FormId)
    name = (menu.Name or "").strip().lower()
    if name == "form management":
        render_form_management()
    elif name == "menu management":
        render_menu_management()
    elif name == "lookup management":
        render_lookup_management()
    elif name == "user management":
        render_user_management()
    else:
        st.title(menu.Name)
        st.info("This menu has no form attached. Add children, or attach a FormId via Menu Management.")


if __name__ == "__main__":
	main()


