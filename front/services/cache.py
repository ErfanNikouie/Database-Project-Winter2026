from __future__ import annotations

from typing import Any, Callable

from services.cache_service import cache


def cache_by_token(
    cache_key: str,
    token_marker: str,
    loader: Callable[..., Any],
    loader_args: tuple,
    loader_kwargs: tuple,
) -> Any:
    cache_key_full = f"{cache_key}:{token_marker}:{loader_args}:{loader_kwargs}"
    cached = cache.get(cache_key_full)
    if cached is not None:
        return cached
    kwargs_dict = {k: v for k, v in loader_kwargs}
    value = loader(*loader_args, **kwargs_dict)
    cache.set(cache_key_full, value, ttl_seconds=60)
    return value


def clear_all_metadata_cache() -> None:
    cache.clear()

