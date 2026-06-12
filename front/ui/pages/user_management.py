from __future__ import annotations

import streamlit as st

from services.user_service import UserService


def render_user_management() -> None:
    st.title("User Management")
    st.caption("Prototype: permissions are stubbed; assume admin has full access.")

    us = UserService()

    users = us.list_users()
    st.subheader("Users")
    if users:
        st.dataframe(
            [
                {
                    "Id": u.Id,
                    "Username": u.Username,
                    "IsActive": u.IsActive,
                    "AccessLevel": u.AccessLevel,
                    "HasConfidentialAccess": u.HasConfidentialAccess,
                }
                for u in users
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No users")

    user_map = {f"{u.Username} (#{u.Id})": u.Id for u in users}
    selected_user_id = st.selectbox(
        "Select user",
        options=[None] + list(user_map.values()),
        format_func=lambda x: "(new)" if x is None else next(k for k, v in user_map.items() if v == x),
    )

    current_user = next((u for u in users if u.Id == selected_user_id), None)

    with st.form("user_edit"):
        username = st.text_input("Username", value=current_user.Username if current_user else "")
        password = st.text_input(
            "Password (stored as PasswordHash for prototype)",
            value="",
            type="password",
            help="Leave blank to keep current password",
        )
        is_active = st.checkbox("IsActive", value=bool(current_user.IsActive) if current_user else True)
        access_level = st.number_input(
            "AccessLevel",
            value=int(current_user.AccessLevel) if current_user else 0,
            step=1,
        )
        confidential = st.checkbox(
            "HasConfidentialAccess",
            value=bool(current_user.HasConfidentialAccess) if current_user else False,
        )

        col1, col2 = st.columns([1, 1])
        save = col1.form_submit_button("Save", type="primary")
        delete = col2.form_submit_button("Delete")

    if save:
        try:
            if not username.strip():
                st.error("Username is required")
            else:
                if current_user is None:
                    us.create_user(
                        username=username,
                        password_hash=password or "admin",
                        is_active=is_active,
                        access_level=int(access_level),
                        has_confidential_access=confidential,
                    )
                    st.success("Created")
                else:
                    us.update_user(
                        current_user.Id,
                        username=username,
                        password_hash=password or None,
                        is_active=is_active,
                        access_level=int(access_level),
                        has_confidential_access=confidential,
                    )
                    st.success("Updated")
                st.rerun()
        except Exception as e:
            st.error(f"Save failed: {e}")

    if delete:
        if current_user is None:
            st.warning("Select a user")
        else:
            try:
                us.delete_user(current_user.Id)
                st.success("Deleted")
                st.rerun()
            except Exception as e:
                st.error(f"Delete failed: {e}")

    st.divider()
    st.subheader("User Groups")

    groups = us.list_groups()
    if groups:
        st.dataframe(
            [{"Id": g.Id, "Name": g.Name, "Description": g.Description} for g in groups],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No groups")

    group_map = {f"{g.Name} (#{g.Id})": g.Id for g in groups}
    selected_group_id = st.selectbox(
        "Select group",
        options=[None] + list(group_map.values()),
        format_func=lambda x: "(new)" if x is None else next(k for k, v in group_map.items() if v == x),
    )

    current_group = next((g for g in groups if g.Id == selected_group_id), None)

    with st.form("group_edit"):
        name = st.text_input("Group Name", value=current_group.Name if current_group else "")
        desc = st.text_area("Group Description", value=current_group.Description if current_group and current_group.Description else "")
        col1, col2 = st.columns([1, 1])
        save_g = col1.form_submit_button("Save Group", type="primary")
        del_g = col2.form_submit_button("Delete Group")

    if save_g:
        try:
            if not name.strip():
                st.error("Group Name is required")
            else:
                if current_group is None:
                    us.create_group(name=name, description=desc)
                    st.success("Created")
                else:
                    us.update_group(current_group.Id, name=name, description=desc)
                    st.success("Updated")
                st.rerun()
        except Exception as e:
            st.error(f"Save failed: {e}")

    if del_g:
        if current_group is None:
            st.warning("Select a group")
        else:
            try:
                us.delete_group(current_group.Id)
                st.success("Deleted")
                st.rerun()
            except Exception as e:
                st.error(f"Delete failed: {e}")

