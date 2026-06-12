from __future__ import annotations

from dash import dcc, html

from layouts.shell import build_shell_layout
from services.session import default_auth_store, default_ui_store


def build_main_layout() -> html.Div:
    return html.Div(
        [
            dcc.Store(id="auth-store", storage_type="session", data=default_auth_store()),
            dcc.Store(id="ui-store", storage_type="session", data=default_ui_store()),
            dcc.Store(id="table-store", storage_type="memory", data={"rows": [], "count": 0}),
            dcc.Store(id="schema-store", storage_type="memory", data={}),
            dcc.Store(id="notifications-store", storage_type="memory", data=[]),
            html.Div(id="notification-host"),
            build_shell_layout(),
        ]
    )

