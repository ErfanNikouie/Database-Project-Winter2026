from __future__ import annotations

from dash import dcc, html, page_container

from layouts.navbar import build_navbar


def build_shell_layout() -> html.Div:
    return html.Div(
        [
            dcc.Location(id="url", refresh=False),
            html.Div(build_navbar(), id="navbar-wrapper"),
            html.Div(
                [
                    html.Div(id="sidebar-wrapper", className="sidebar-wrapper"),
                    html.Main(
                        dcc.Loading(id="page-loader", type="dot", children=[html.Div(id="page-host", children=[page_container])]),
                        className="content-wrapper",
                    ),
                ],
                className="shell-body",
            ),
        ],
        className="app-shell",
    )


