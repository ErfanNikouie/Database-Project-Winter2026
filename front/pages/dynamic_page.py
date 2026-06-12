from __future__ import annotations

import dash
import dash_mantine_components as dmc
from dash import dcc, html

from components.dynamic_table import build_empty_grid

dash.register_page(__name__, path_template="/menu/<menu_id>", name="Dynamic Page")


def layout(menu_id: str | None = None) -> html.Div:
    return html.Div(
        [
            dcc.Store(id="active-menu-id", data=menu_id),
            dmc.Group(
                [
                    dmc.Title(id="dynamic-page-title", order=2),
                    dmc.Badge(id="dynamic-page-table", color="indigo", variant="light"),
                ],
                justify="space-between",
                mb="md",
            ),
            html.Div(id="dynamic-filter-section"),
            html.Div(id="dynamic-toolbar"),
            html.Div(id="dynamic-grid-wrapper", children=build_empty_grid()),
            html.Div(id="dynamic-page-error", className="page-error"),
        ],
        className="dynamic-page",
    )


