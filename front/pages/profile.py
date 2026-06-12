from __future__ import annotations

import streamlit as st

from api.profile import get_current_user, update_current_user
from components.notifications import show_api_error, show_success
from utils.models import ApiError, ProfileUpdatePayload


def render_profile_page(*, base_url: str, access_token: str) -> None:
    st.title("My Profile")

    try:
        user = get_current_user(base_url=base_url, access_token=access_token)
    except ApiError as exc:
        show_api_error(exc.message, exc.field)
        return

    with st.form("profile-form"):
        username = st.text_input("Username", value=user.get("username", ""))
        st.text_input("Active", value=str(user.get("is_active", False)), disabled=True)
        st.text_input("Groups", value=", ".join(group["name"] for group in user.get("groups", [])), disabled=True)

        st.markdown("### Change password")
        current_password = st.text_input("Current password", type="password")
        new_password = st.text_input("New password", type="password")
        confirm_new_password = st.text_input("Confirm new password", type="password")

        submitted = st.form_submit_button("Save profile", use_container_width=True)

    if not submitted:
        return

    try:
        payload = ProfileUpdatePayload(
            username=username,
            current_password=current_password or None,
            new_password=new_password or None,
            confirm_new_password=confirm_new_password or None,
        ).model_dump(exclude_none=True)
        updated = update_current_user(base_url=base_url, access_token=access_token, payload=payload)
        st.session_state.current_user = updated
        show_success("Profile updated")
    except ApiError as exc:
        show_api_error(exc.message, exc.field)
    except Exception as exc:
        show_api_error(str(exc))

