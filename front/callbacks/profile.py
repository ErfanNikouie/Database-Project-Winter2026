from __future__ import annotations

from dash import Input, Output, State, callback, no_update

from services.api_client import api_client
from utils.models import ApiError


@callback(
    Output("profile-username", "value"),
    Output("profile-active", "value"),
    Output("profile-groups", "value"),
    Output("profile-error", "children"),
    Input("_pages_location", "pathname"),
    State("auth-store", "data"),
    prevent_initial_call=False,
)
def load_profile(pathname: str, auth_data: dict):
    if pathname != "/profile":
        return no_update, no_update, no_update, no_update
    if not auth_data or not auth_data.get("authenticated"):
        return "", "", "", "Unauthorized"
    try:
        user = api_client.get_current_user(base_url=_base_url(), access_token=auth_data["access_token"])
        groups = ", ".join(group["name"] for group in user.get("groups", []))
        return user.get("username", ""), str(user.get("is_active", False)), groups, ""
    except ApiError as exc:
        return "", "", "", exc.message


@callback(
    Output("profile-error", "children", allow_duplicate=True),
    Input("profile-save", "n_clicks"),
    State("auth-store", "data"),
    State("profile-username", "value"),
    State("profile-current-password", "value"),
    State("profile-new-password", "value"),
    State("profile-confirm-password", "value"),
    prevent_initial_call=True,
)
def save_profile(
    n_clicks: int | None,
    auth_data: dict,
    username: str | None,
    current_password: str | None,
    new_password: str | None,
    confirm_password: str | None,
):
    if not n_clicks:
        return no_update
    if not auth_data or not auth_data.get("authenticated"):
        return "Unauthorized"

    payload = {"username": username}
    if any([current_password, new_password, confirm_password]):
        payload.update(
            {
                "current_password": current_password,
                "new_password": new_password,
                "confirm_new_password": confirm_password,
            }
        )

    try:
        api_client.update_current_user(
            base_url=_base_url(),
            access_token=auth_data["access_token"],
            payload=payload,
        )
        return "Profile updated"
    except ApiError as exc:
        return exc.message


def _base_url() -> str:
    from api.base import DEFAULT_BASE_URL

    return DEFAULT_BASE_URL

