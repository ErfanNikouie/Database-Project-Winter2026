from __future__ import annotations

import streamlit as st

from api.auth import get_current_user, login
from components.notifications import show_api_error
from services.session import set_auth
from utils.models import ApiError


def render_login_page(*, base_url: str) -> None:
    left, center, right = st.columns([1, 1.4, 1])
    with center:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("## Welcome back")
        st.caption("Sign in to HRMS Dynamic Enterprise Platform")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        remember_me = st.checkbox("Remember me", value=True)
        submitted = st.button("Login", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if not submitted:
        return

    try:
        with st.spinner("Signing in..."):
            data = login(base_url=base_url, username=username, password=password)
            user_payload = data.get("user") or {}
            if remember_me:
                try:
                    # Refresh profile payload on login to keep sidebar/profile in sync.
                    user_payload = get_current_user(base_url=base_url, access_token=data["access"])
                except ApiError:
                    pass
            set_auth(data["access"], data["refresh"], user_payload)
        st.rerun()
    except ApiError as exc:
        show_api_error(exc.message, exc.field)

