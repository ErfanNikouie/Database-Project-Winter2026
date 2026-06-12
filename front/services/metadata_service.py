from __future__ import annotations

from services.api_client import api_client
from services.cache_service import cache


def fetch_metadata_version(*, base_url: str, access_token: str) -> str:
    return api_client.get_metadata_version(base_url=base_url, access_token=access_token)


def fetch_form_schema(*, base_url: str, access_token: str, metadata_version: str, table_name: str) -> dict:
    cache_key = f"form_schema:{metadata_version}:{table_name}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    schema = api_client.get_form_schema(base_url=base_url, access_token=access_token, form_name=table_name)
    cache.set(cache_key, schema, ttl_seconds=600)
    return schema


def fetch_lookup_values(*, base_url: str, access_token: str, metadata_version: str, lookup_id: int) -> list[dict]:
    cache_key = f"lookup_values:{metadata_version}:{lookup_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    data = api_client.list_rows(
        base_url=base_url,
        access_token=access_token,
        payload={
            "menu": "Lookup Values",
            "limit": 1000,
            "offset": 0,
            "sort_by": "value",
            "sort_direction": "asc",
            "filters": {"lookup_id": lookup_id},
        },
    )
    items = data.get("items", [])
    cache.set(cache_key, items, ttl_seconds=600)
    return items


def clear_metadata_cache() -> None:
    cache.clear()

