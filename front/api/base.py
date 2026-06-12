from __future__ import annotations

import os
from typing import Any

import requests
from dotenv import load_dotenv

from utils.models import ApiError

load_dotenv()

DEFAULT_BASE_URL = os.getenv("HRMS_BACKEND_URL", "http://127.0.0.1:8000")
DEFAULT_TIMEOUT = int(os.getenv("HRMS_REQUEST_TIMEOUT", "30"))


def request_json(
    *,
    method: str,
    path: str,
    base_url: str | None = None,
    access_token: str | None = None,
    payload: dict[str, Any] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    url = f"{(base_url or DEFAULT_BASE_URL).rstrip('/')}{path}"
    headers = {"Content-Type": "application/json"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    try:
        response = requests.request(method=method, url=url, json=payload, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        raise ApiError(f"Network error: {exc}") from exc

    try:
        body = response.json()
    except ValueError:
        body = {"success": False, "error": {"message": response.text or "Unexpected non-JSON response"}}

    if response.status_code >= 400 or not body.get("success", False):
        error = body.get("error") or {}
        raise ApiError(
            message=error.get("message") or f"Request failed with status {response.status_code}",
            field=error.get("field"),
            status_code=response.status_code,
        )

    return body.get("data", {})

