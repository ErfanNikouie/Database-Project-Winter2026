from __future__ import annotations

import streamlit as st


def show_success(message: str) -> None:
    st.toast(message, icon="✅")


def show_error(message: str) -> None:
    st.error(message)


def show_api_error(error_message: str, field: str | None = None) -> None:
    if field:
        st.error(f"{error_message} (field: {field})")
    else:
        st.error(error_message)

