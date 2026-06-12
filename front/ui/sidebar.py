from __future__ import annotations

from typing import Callable

import streamlit as st

from services.menu_service import MenuNode


def render_sidebar(
    menu_tree: list[MenuNode],
    *,
    on_menu_selected: Callable[[int], None],
    on_initialize: Callable[[], None],
) -> None:
    """Render recursive sidebar navigation."""

    st.sidebar.title("Navigation")

    def render_nodes(container, nodes: list[MenuNode]) -> None:
        for node in nodes:
            m = node.menu
            has_children = len(node.children) > 0

            if has_children:
                exp = container.expander(m.Name, expanded=False)
                # A parent can also be a clickable menu if it has a FormId
                if m.FormId is not None:
                    if exp.button(f"Open: {m.Name}", key=f"open_menu_{m.Id}"):
                        on_menu_selected(int(m.Id))
                render_nodes(exp, node.children)
            else:
                if container.button(m.Name, key=f"menu_{m.Id}"):
                    on_menu_selected(int(m.Id))

    if not menu_tree:
        st.sidebar.info("No menus found.")
    else:
        render_nodes(st.sidebar, menu_tree)

    st.sidebar.divider()
    if st.sidebar.button("Initialize", type="primary"):
        on_initialize()

