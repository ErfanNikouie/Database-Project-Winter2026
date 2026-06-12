from __future__ import annotations

from services.api_client import api_client
from services.cache_service import cache


def fetch_menu_tree(*, base_url: str, access_token: str, etag: str | None) -> tuple[list[dict], str | None]:
    cached = cache.get("menu_tree")
    if cached and etag and cached.get("etag") == etag:
        return cached["items"], etag

    items, next_etag = api_client.get_menu_tree(base_url=base_url, access_token=access_token, etag=etag)
    if items is None:
        if cached:
            return cached["items"], etag
        # ETag might be valid while in-memory cache is cold (app restart).
        items, next_etag = api_client.get_menu_tree(base_url=base_url, access_token=access_token, etag=None)
        if items is None:
            return [], etag

    cache.set("menu_tree", {"items": items, "etag": next_etag}, ttl_seconds=300)
    return items, next_etag

