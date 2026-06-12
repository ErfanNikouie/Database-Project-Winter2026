from __future__ import annotations

from api.base import request_json
from utils.models import LoginPayload


def login(*, base_url: str, username: str, password: str) -> dict:
    payload = LoginPayload(username=username, password=password).model_dump()
    return request_json(method="POST", path="/api/auth/login", base_url=base_url, payload=payload)


def refresh_access_token(*, base_url: str, refresh_token: str) -> str:
    data = request_json(
        method="POST",
        path="/api/auth/refresh",
        base_url=base_url,
        payload={"refresh": refresh_token},
    )
    return data["access"]


def logout(*, base_url: str, access_token: str, refresh_token: str) -> None:
    request_json(
        method="POST",
        path="/api/auth/logout",
        base_url=base_url,
        access_token=access_token,
        payload={"refresh": refresh_token},
    )


def get_current_user(*, base_url: str, access_token: str) -> dict:
    return request_json(method="GET", path="/api/auth/me", base_url=base_url, access_token=access_token)


def update_current_user(*, base_url: str, access_token: str, payload: dict) -> dict:
    return request_json(
        method="POST",
        path="/api/auth/me",
        base_url=base_url,
        access_token=access_token,
        payload=payload,
    )

