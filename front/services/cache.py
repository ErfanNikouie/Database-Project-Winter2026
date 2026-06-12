from __future__ import annotations

import streamlit as st


@st.cache_data(ttl=60, show_spinner=False)
def cache_by_token(cache_key: str, token_marker: str, loader_args: tuple, loader_kwargs: tuple):
    loader = st.session_state.get(cache_key)
    if not callable(loader):
        raise RuntimeError(f"Missing cache loader: {cache_key}")
    kwargs_dict = {k: v for k, v in loader_kwargs}
    return loader(*loader_args, **kwargs_dict)


def clear_all_metadata_cache() -> None:
    st.cache_data.clear()

