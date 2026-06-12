from __future__ import annotations

from dash import Input, Output, State, callback, no_update

from services.api_client import api_client
from services.auth_service import build_auth_payload, empty_auth_payload
from utils.models import ApiError


@callback(
    Output("auth-store", "data", allow_duplicate=True),
    Output("login-error", "children"),
    Output("url", "pathname", allow_duplicate=True),
    Input("login-submit", "n_clicks"),
    State("login-username", "value"),
    State("login-password", "value"),
    prevent_initial_call=True,
)
def handle_login(n_clicks: int | None, username: str | None, password: str | None):
    if not n_clicks:
        return no_update, no_update, no_update
    if not username or not password:
        return no_update, "Username and password are required", no_update

    try:
        data = api_client.login(base_url=_base_url(), username=username, password=password)
        user = api_client.get_current_user(base_url=_base_url(), access_token=data["access"])
        return build_auth_payload(access_token=data["access"], refresh_token=data["refresh"], user=user), "", "/"
    except ApiError as exc:
        return empty_auth_payload(), exc.message, no_update


@callback(
    Output("auth-store", "data", allow_duplicate=True),
    Output("url", "pathname", allow_duplicate=True),
    Input("btn-logout", "n_clicks"),
    State("auth-store", "data"),
    prevent_initial_call=True,
)
def handle_logout(n_clicks: int | None, auth_data: dict):
    if not n_clicks:
        return no_update, no_update
    try:
        access = auth_data.get("access_token")
        refresh = auth_data.get("refresh_token")
        if access and refresh:
            api_client.logout(base_url=_base_url(), access_token=access, refresh_token=refresh)
    except ApiError:
        pass
    return empty_auth_payload(), "/login"


def _base_url() -> str:
    from api.base import DEFAULT_BASE_URL

    return DEFAULT_BASE_URL

