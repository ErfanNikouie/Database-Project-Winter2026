from __future__ import annotations

import streamlit as st

from api.crud import list_options, list_rows
from api.forms import get_form_schema
from api.system import get_metadata_version


@st.cache_data(ttl=300, show_spinner=False)
def load_form_schema_cached(base_url: str, token: str, metadata_version: str, form_name: str) -> dict:
    _ = metadata_version
    return get_form_schema(base_url=base_url, access_token=token, form_name=form_name)


@st.cache_data(ttl=300, show_spinner=False)
def load_lookup_values_cached(
    base_url: str,
    token: str,
    metadata_version: str,
    lookup_id: int,
    query: str = "",
    limit: int = 100,
) -> list[dict]:
    _ = metadata_version
    response = list_rows(
        base_url=base_url,
        access_token=token,
        payload={
            "menu": "Lookup Values",
            "limit": max(limit, 1000),
            "offset": 0,
            "sort_by": "value",
            "sort_direction": "asc",
            "filters": {"lookup_id": lookup_id},
        },
    )
    items = response["items"]
    search = query.strip().lower()
    if not search:
        return items[:limit]
    return [item for item in items if search in str(item.get("value", "")).lower()][:limit]


@st.cache_data(ttl=300, show_spinner=False)
def load_foreign_key_options_cached(
    base_url: str,
    token: str,
    metadata_version: str,
    foreign_key_table: str,
    query: str,
    limit: int,
) -> list[dict]:
    _ = metadata_version
    return list_options(
        base_url=base_url,
        access_token=token,
        payload={"table": foreign_key_table, "query": query, "limit": limit},
    )


@st.cache_data(ttl=300, show_spinner=False)
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
    items = list_options(
        base_url=base_url,
        access_token=token,
        payload={"table": foreign_key_table, "ids": list(ids), "limit": max(20, len(ids))},
    )
    return {int(item["id"]): str(item["label"]) for item in items}


def refresh_metadata_version(*, base_url: str, access_token: str) -> str:
    return get_metadata_version(base_url=base_url, access_token=access_token)


def clear_metadata_cache() -> None:
    st.cache_data.clear()

