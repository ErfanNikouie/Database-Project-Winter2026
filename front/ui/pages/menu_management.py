from __future__ import annotations

import streamlit as st

from services.form_service import FormService
from services.menu_service import MenuService


def render_menu_management() -> None:
    st.title("Menu Management")

    ms = MenuService()
    fs = FormService()

    menus = ms.list_menus()
    forms = fs.list_forms()

    st.subheader("Existing menus")
    if menus:
        st.dataframe(
            [
                {
                    "Id": m.Id,
                    "Name": m.Name,
                    "ParentId": m.ParentId,
                    "FormId": m.FormId,
                }
                for m in menus
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No menus yet.")

    menu_map = {f"{m.Name} (#{m.Id})": m.Id for m in menus}
    selected_menu_id = st.selectbox(
        "Select menu",
        options=[None] + list(menu_map.values()),
        format_func=lambda x: "(new)" if x is None else next(k for k, v in menu_map.items() if v == x),
    )

    current = ms.get_menu(selected_menu_id) if selected_menu_id else None

    parent_options: dict[str, int | None] = {"(none)": None}
    for m in menus:
        parent_options[f"{m.Name} (#{m.Id})"] = m.Id

    form_options: dict[str, int | None] = {"(none)": None}
    for f in forms:
        form_options[f"{f.Name} (#{f.Id})"] = f.Id

    with st.form("menu_edit"):
        name = st.text_input("Name", value=current.Name if current else "")

        parent_id = st.selectbox(
            "Parent",
            options=list(parent_options.values()),
            format_func=lambda x: next(k for k, v in parent_options.items() if v == x),
            index=list(parent_options.values()).index(current.ParentId) if current and current.ParentId in parent_options.values() else 0,
        )

        form_id = st.selectbox(
            "Form",
            options=list(form_options.values()),
            format_func=lambda x: next(k for k, v in form_options.items() if v == x),
            index=list(form_options.values()).index(current.FormId) if current and current.FormId in form_options.values() else 0,
        )

        col1, col2 = st.columns([1, 1])
        save = col1.form_submit_button("Save", type="primary")
        delete = col2.form_submit_button("Delete")

    if save:
        try:
            if not name.strip():
                st.error("Name is required")
            else:
                if current is None:
                    ms.create_menu(name=name, parent_id=parent_id, form_id=form_id)
                    st.success("Created")
                else:
                    # prevent cycles (simple check)
                    if parent_id == current.Id:
                        st.error("A menu cannot be its own parent")
                    else:
                        ms.update_menu(current.Id, name=name, parent_id=parent_id, form_id=form_id)
                        st.success("Updated")
                st.rerun()
        except Exception as e:
            st.error(f"Save failed: {e}")

    if delete:
        if current is None:
            st.warning("Select a menu")
        else:
            try:
                ms.delete_menu(current.Id)
                st.success("Deleted")
                st.rerun()
            except Exception as e:
                st.error(f"Delete failed: {e}")

