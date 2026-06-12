from __future__ import annotations

from typing import Any

from services.api_client import api_client


def build_auth_payload(*, access_token: str, refresh_token: str, user: dict[str, Any]) -> dict[str, Any]:
    return {
        "authenticated": True,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user,
    }


def empty_auth_payload() -> dict[str, Any]:
    return {
        "authenticated": False,
        "access_token": None,
        "refresh_token": None,
        "user": None,
    }


def refresh_session(*, base_url: str, auth_data: dict[str, Any]) -> dict[str, Any]:
    refresh_token = auth_data.get("refresh_token")
    if not refresh_token:
        return empty_auth_payload()
    access_token = api_client.refresh_access_token(base_url=base_url, refresh_token=refresh_token)
    user = api_client.get_current_user(base_url=base_url, access_token=access_token)
    return build_auth_payload(access_token=access_token, refresh_token=refresh_token, user=user)

