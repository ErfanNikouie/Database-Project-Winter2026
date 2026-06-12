from __future__ import annotations

import requests

from api.base import DEFAULT_TIMEOUT
from utils.models import ApiError


def get_menu_tree(*, base_url: str, access_token: str, etag: str | None = None) -> tuple[list[dict] | None, str | None]:
    url = f"{base_url.rstrip('/')}/api/menus/tree"
    headers = {"Authorization": f"Bearer {access_token}"}
    if etag:
        headers["If-None-Match"] = etag

    try:
        response = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
    except requests.RequestException as exc:
        raise ApiError(f"Network error: {exc}") from exc

    if response.status_code == 304:
        return None, etag

    try:
        body = response.json()
    except ValueError as exc:
        raise ApiError("Invalid response from menu endpoint", status_code=response.status_code) from exc

    if response.status_code >= 400 or not body.get("success", False):
        error = body.get("error") or {}
        raise ApiError(
            message=error.get("message") or f"Request failed with status {response.status_code}",
            field=error.get("field"),
            status_code=response.status_code,
        )

    return body.get("data", {}).get("items", []), response.headers.get("ETag")

