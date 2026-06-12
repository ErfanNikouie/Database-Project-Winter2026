from __future__ import annotations

from dash import Input, Output, callback, no_update


PUBLIC_PATHS = {"/login"}


@callback(
    Output("_pages_location", "pathname", allow_duplicate=True),
    Input("auth-store", "data"),
    Input("_pages_location", "pathname"),
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
    Output("shell-body-wrapper", "style"),
    Output("content-wrapper", "style"),
    Input("_pages_location", "pathname"),
)
def toggle_shell_chrome(pathname: str):
    if pathname == "/login":
        return (
            {"display": "none"},
            {"display": "none"},
            {"gridTemplateColumns": "1fr", "minHeight": "100vh"},
            {"padding": "0", "minHeight": "100vh"},
        )
    return ({"display": "block"}, {"display": "block"}, {}, {})


@callback(
    Output("_pages_location", "pathname", allow_duplicate=True),
    Input("btn-profile", "n_clicks"),
    prevent_initial_call=True,
)
def open_profile_page(n_clicks: int | None):
    if not n_clicks:
        return no_update
    return "/profile"


@callback(
    Output("active-menu-id", "data"),
    Input("_pages_location", "pathname"),
    prevent_initial_call=False,
)
def sync_active_menu_id(pathname: str | None):
    if not pathname or not pathname.startswith("/menu/"):
        return no_update
    try:
        return int(pathname.rsplit("/", maxsplit=1)[-1])
    except ValueError:
        return no_update


