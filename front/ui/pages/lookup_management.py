from __future__ import annotations

import streamlit as st

from services.lookup_service import LookupService


def render_lookup_management() -> None:
    st.title("Lookup Management")

    ls = LookupService()

    lookups = ls.list_lookups()

    st.subheader("Lookups")
    if lookups:
        st.dataframe(
            [{"Id": l.Id, "Name": l.Name, "Description": l.Description} for l in lookups],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No lookups yet.")

    lookup_map = {f"{(l.Name or l.Description)} (#{l.Id})": l.Id for l in lookups}
    selected_lookup_id = st.selectbox(
        "Select lookup",
        options=[None] + list(lookup_map.values()),
        format_func=lambda x: "(new)" if x is None else next(k for k, v in lookup_map.items() if v == x),
    )

    current = ls.get_lookup(selected_lookup_id) if selected_lookup_id else None

    with st.form("lookup_edit"):
        name = st.text_input("Name", value=current.Name if current and current.Name else "")
        desc = st.text_input("Description", value=current.Description if current else "")
        col1, col2 = st.columns([1, 1])
        save = col1.form_submit_button("Save", type="primary")
        delete = col2.form_submit_button("Delete")

    if save:
        try:
            if not desc.strip():
                st.error("Description is required")
            else:
                if current is None:
                    ls.create_lookup(name=name, description=desc)
                    st.success("Created")
                else:
                    ls.update_lookup(current.Id, name=name, description=desc)
                    st.success("Updated")
                st.rerun()
        except Exception as e:
            st.error(f"Save failed: {e}")

    if delete:
        if current is None:
            st.warning("Select a lookup")
        else:
            try:
                ls.delete_lookup(current.Id)
                st.success("Deleted")
                st.rerun()
            except Exception as e:
                st.error(f"Delete failed: {e}")

    if current is None:
        st.info("Select a lookup to manage its values.")
        return

    st.divider()
    st.subheader("Lookup Values")

    values = ls.list_values(current.Id)
    if values:
        st.dataframe(
            [{"Id": v.Id, "Value": v.Value} for v in values],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No values yet.")

    value_map = {f"{v.Value} (#{v.Id})": v.Id for v in values}
    selected_value_id = st.selectbox(
        "Select value",
        options=[None] + list(value_map.values()),
        format_func=lambda x: "(new)" if x is None else next(k for k, v in value_map.items() if v == x),
    )

    current_value = next((v for v in values if v.Id == selected_value_id), None)

    with st.form("value_edit"):
        value_text = st.text_input("Value", value=current_value.Value if current_value else "")
        col1, col2 = st.columns([1, 1])
        save_v = col1.form_submit_button("Save Value", type="primary")
        delete_v = col2.form_submit_button("Delete Value")

    if save_v:
        try:
            if not value_text.strip():
                st.error("Value is required")
            else:
                if current_value is None:
                    ls.create_value(current.Id, value_text)
                    st.success("Created")
                else:
                    ls.update_value(current_value.Id, value=value_text)
                    st.success("Updated")
                st.rerun()
        except Exception as e:
            st.error(f"Save failed: {e}")

    if delete_v:
        if current_value is None:
            st.warning("Select a value")
        else:
            try:
                ls.delete_value(current_value.Id)
                st.success("Deleted")
                st.rerun()
            except Exception as e:
                st.error(f"Delete failed: {e}")

