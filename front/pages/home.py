from __future__ import annotations

import dash
import dash_mantine_components as dmc
from dash import html

dash.register_page(__name__, path="/", name="Home")


def layout() -> html.Div:
    return html.Div(
        dmc.Stack(
            [
                dmc.Title("HRMS Dynamic Platform", order=2),
                dmc.Text("Select a menu item to open a metadata-driven form page.", c="dimmed"),
            ],
            gap="sm",
        ),
        className="home-page",
    )

