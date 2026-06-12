from __future__ import annotations

from typing import Any

import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify


def build_sidebar(menu_tree: list[dict[str, Any]], selected_menu_id: int | None) -> html.Div:
    if not menu_tree:
        return html.Div(dmc.Text("No menus", c="dimmed"), className="sidebar-body")

    return html.Div(
        [
            dmc.Text("Navigation", fw=600, mb="sm"),
            html.Div([_build_menu_node(node, selected_menu_id) for node in menu_tree], className="menu-tree"),
        ],
        className="sidebar-body",
    )


def _build_menu_node(node: dict[str, Any], selected_menu_id: int | None):
    children = node.get("children") or []
    form = node.get("form")

    if children:
        return dmc.Accordion(
            [
                dmc.AccordionItem(
                    [
                        dmc.AccordionControl(node["name"], icon=DashIconify(icon="mdi:folder")),
                        dmc.AccordionPanel([
                            _build_menu_node(child, selected_menu_id) for child in children
                        ]),
                    ],
                    value=f"menu-folder-{node['id']}",
                )
            ],
            variant="contained",
            radius="md",
            className="menu-folder",
        )

    if not form:
        return dmc.Text(node["name"], c="dimmed")

    href = f"/menu/{node['id']}"
    is_active = selected_menu_id == node["id"]
    return dmc.Anchor(
        dmc.Button(
            node["name"],
            fullWidth=True,
            justify="space-between",
            leftSection=DashIconify(icon="mdi:table", width=16),
            variant="filled" if is_active else "light",
            color="green" if is_active else "indigo",
            className="menu-link-button",
        ),
        href=href,
        underline="never",
    )

