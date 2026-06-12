from __future__ import annotations

from dash import Input, Output, callback, no_update


PUBLIC_PATHS = {"/login"}


@callback(
    Output("url", "pathname", allow_duplicate=True),
    Input("auth-store", "data"),
    Input("url", "pathname"),
    prevent_initial_call=True,
)
def guard_routes(auth_data: dict, pathname: str):
    authenticated = bool((auth_data or {}).get("authenticated"))
    path = pathname or "/"

    if not authenticated and path not in PUBLIC_PATHS:
        return "/login"

    if authenticated and path == "/login":
        return "/"

    return no_update


@callback(
    Output("navbar-wrapper", "style"),
    Output("sidebar-wrapper", "style"),
    Input("url", "pathname"),
)
def toggle_shell_chrome(pathname: str):
    if pathname == "/login":
        return {"display": "none"}, {"display": "none"}
    return {"display": "block"}, {"display": "block"}


@callback(
    Output("url", "pathname", allow_duplicate=True),
    Input("btn-profile", "n_clicks"),
    prevent_initial_call=True,
)
def open_profile_page(n_clicks: int | None):
    if not n_clicks:
        return no_update
    return "/profile"


