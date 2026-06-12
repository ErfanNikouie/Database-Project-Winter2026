from __future__ import annotations

from typing import Any

from api.base import request_json
from utils.models import DataListPayload, DataWritePayload, DetailPayload


def insert_row(*, base_url: str, access_token: str, payload: dict[str, Any]) -> dict:
    validated = DataWritePayload(**payload).model_dump(exclude_none=True)
    return request_json(
        method="POST",
        path="/api/data/insert",
        base_url=base_url,
        access_token=access_token,
        payload=validated,
    )


def update_row(*, base_url: str, access_token: str, payload: dict[str, Any]) -> dict:
    validated = DataWritePayload(**payload).model_dump(exclude_none=True)
    return request_json(
        method="POST",
        path="/api/data/update",
        base_url=base_url,
        access_token=access_token,
        payload=validated,
    )


def delete_row(*, base_url: str, access_token: str, payload: dict[str, Any]) -> dict:
    validated = DataWritePayload(**payload).model_dump(exclude_none=True)
    return request_json(
        method="POST",
        path="/api/data/delete",
        base_url=base_url,
        access_token=access_token,
        payload=validated,
    )


def detail_row(*, base_url: str, access_token: str, payload: dict[str, Any]) -> dict:
    validated = DetailPayload(**payload).model_dump(exclude_none=True)
    return request_json(
        method="POST",
        path="/api/data/detail",
        base_url=base_url,
        access_token=access_token,
        payload=validated,
    )


def list_rows(*, base_url: str, access_token: str, payload: dict[str, Any]) -> dict:
    validated = DataListPayload(**payload).model_dump(exclude_none=True)
    return request_json(
        method="POST",
        path="/api/data/list",
        base_url=base_url,
        access_token=access_token,
        payload=validated,
    )


def list_options(*, base_url: str, access_token: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = request_json(
        method="POST",
        path="/api/data/options",
        base_url=base_url,
        access_token=access_token,
        payload=payload,
    )
    return data.get("items", [])


