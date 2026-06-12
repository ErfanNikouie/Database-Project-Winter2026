from __future__ import annotations

import requests

from api.base import DEFAULT_TIMEOUT
from utils.models import ApiError


def get_form_schema(*, base_url: str, access_token: str, form_name: str) -> dict:
    url = f"{base_url.rstrip('/')}/api/forms/{form_name}/schema"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        response = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
    except requests.RequestException as exc:
        raise ApiError(f"Network error: {exc}") from exc

    try:
        body = response.json()
    except ValueError as exc:
        raise ApiError("Invalid schema response payload", status_code=response.status_code) from exc

    if response.status_code >= 400:
        error = body.get("error") if isinstance(body, dict) else {}
        raise ApiError(
            message=(error or {}).get("message") or f"Request failed with status {response.status_code}",
            field=(error or {}).get("field"),
            status_code=response.status_code,
        )

    # Form schema endpoint returns a direct object (not success/data envelope).
    if isinstance(body, dict) and "form" in body and "fields" in body:
        return body

    # Forward-compatible fallback if backend later wraps this endpoint.
    if isinstance(body, dict) and body.get("success") is True and isinstance(body.get("data"), dict):
        return body["data"]

    raise ApiError("Unexpected schema response format", status_code=response.status_code)

