from __future__ import annotations

from typing import Any

from api.base import request_json


def get_available_reports(*, base_url: str, access_token: str) -> list[dict[str, Any]]:
    data = request_json(
        method="GET",
        path="/api/reports/available",
        base_url=base_url,
        access_token=access_token,
    )
    return data.get("items", [])


def run_report(*, base_url: str, access_token: str, payload: dict[str, Any]) -> dict[str, Any]:
    return request_json(
        method="POST",
        path="/api/reports/run",
        base_url=base_url,
        access_token=access_token,
        payload=payload,
    )

