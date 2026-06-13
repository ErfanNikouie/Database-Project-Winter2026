from __future__ import annotations

import dash
import dash_mantine_components as dmc
from dash import html

from components.dynamic_page_placeholders import build_dynamic_page_placeholders

dash.register_page(__name__, path="/error", name="Error")


def layout() -> html.Div:
    return html.Div(
        [
            dmc.Alert(
                title="Page error",
                color="red",
                children="The requested page could not be loaded.",
            ),
            build_dynamic_page_placeholders(),
        ]
    )

