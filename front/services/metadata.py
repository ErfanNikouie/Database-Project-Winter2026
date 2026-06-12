from __future__ import annotations

from services.api_client import api_client
from services.metadata_service import clear_metadata_cache, fetch_form_schema, fetch_lookup_values


def load_form_schema_cached(base_url: str, token: str, metadata_version: str, form_name: str) -> dict:
    return fetch_form_schema(
        base_url=base_url,
        access_token=token,
        metadata_version=metadata_version,
        table_name=form_name,
    )


def load_lookup_values_cached(
    base_url: str,
    token: str,
    metadata_version: str,
    lookup_id: int,
    query: str = "",
    limit: int = 100,
) -> list[dict]:
    items = fetch_lookup_values(
        base_url=base_url,
        access_token=token,
        metadata_version=metadata_version,
        lookup_id=lookup_id,
    )
    lowered = query.strip().lower()
    if not lowered:
        return items[:limit]
    return [item for item in items if lowered in str(item.get("value", "")).lower()][:limit]


def load_foreign_key_options_cached(
    base_url: str,
    token: str,
    metadata_version: str,
    foreign_key_table: str,
    query: str,
    limit: int,
) -> list[dict]:
    _ = metadata_version
    return api_client.list_options(
        base_url=base_url,
        access_token=token,
        payload={"table": foreign_key_table, "query": query, "limit": limit},
    )


def load_foreign_key_labels_cached(
    base_url: str,
    token: str,
    metadata_version: str,
    foreign_key_table: str,
    ids: tuple[int, ...],
) -> dict[int, str]:
    _ = metadata_version
    if not ids:
        return {}
    rows = api_client.list_options(
        base_url=base_url,
        access_token=token,
        payload={"table": foreign_key_table, "ids": list(ids), "limit": max(20, len(ids))},
    )
    return {int(row["id"]): str(row["label"]) for row in rows}


def refresh_metadata_version(*, base_url: str, access_token: str) -> str:
    return api_client.get_metadata_version(base_url=base_url, access_token=access_token)

