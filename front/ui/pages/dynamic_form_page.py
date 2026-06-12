from __future__ import annotations

import streamlit as st

from services.crud_service import CrudService
from services.form_service import FormService
from ui.form_renderer import render_dynamic_inputs


def _dialog_supported() -> bool:
    return hasattr(st, "dialog")


def render_dynamic_form(form_id: int) -> None:
    form_service = FormService()
    result = form_service.get_form_with_fields(form_id)
    if result is None:
        st.error("Form not found")
        return

    form, fields = result

    st.title(form.Name)
    if form.Description:
        st.caption(form.Description)

    crud = CrudService()

    # Ensure table exists and schema is synced
    try:
        crud.ensure_table_for_form(form, fields)
    except Exception as e:
        st.error(f"Failed to sync table '{form.TableName}': {e}")
        return

    # Refresh/sync button
    col_a, col_b, col_c, col_d, col_e = st.columns([1, 1, 1, 1, 1])
    if col_a.button("Refresh"):
        st.rerun()

    # List
    try:
        list_result = crud.list_rows(form.TableName)
    except Exception as e:
        st.error(f"Failed to load records: {e}")
        return

    st.subheader("Records")
    if list_result.df.empty:
        st.info("No records yet.")
    else:
        st.dataframe(list_result.df, use_container_width=True, hide_index=True)

    ids: list[int] = []
    if not list_result.df.empty and "Id" in list_result.df.columns:
        ids = [int(x) for x in list_result.df["Id"].tolist()]

    selected_for_edit = None
    if ids:
        selected_for_edit = st.selectbox("Select a record to edit", options=[None] + ids)

    selected_for_delete: list[int] = []
    if ids:
        selected_for_delete = st.multiselect("Select record(s) to delete", options=ids)

    # Actions
    actions = st.columns([1, 1, 1, 1])

    def do_add_dialog() -> None:
        st.subheader("Add")
        data, errors = render_dynamic_inputs(fields, values={}, key_prefix=f"add_{form.Id}")
        if errors:
            st.warning("\n".join(errors))
        if st.button("Save", type="primary"):
            if errors:
                st.stop()
            try:
                crud.insert_row(form.TableName, data)
                st.success("Record added")
                st.rerun()
            except Exception as e:
                st.error(f"Insert failed: {e}")

    def do_edit_dialog(row_id: int) -> None:
        st.subheader(f"Edit (Id={row_id})")
        existing = crud.get_row(form.TableName, row_id) or {}
        data, errors = render_dynamic_inputs(fields, values=existing, key_prefix=f"edit_{form.Id}_{row_id}")
        if errors:
            st.warning("\n".join(errors))
        if st.button("Save", type="primary"):
            if errors:
                st.stop()
            try:
                crud.update_row(form.TableName, row_id, data)
                st.success("Record updated")
                st.rerun()
            except Exception as e:
                st.error(f"Update failed: {e}")

    def do_delete_dialog(row_ids: list[int]) -> None:
        st.subheader("Confirm delete")
        st.write(f"You are about to delete {len(row_ids)} record(s): {row_ids}")
        if st.button("Delete", type="primary"):
            try:
                crud.delete_rows(form.TableName, row_ids)
                st.success("Deleted")
                st.rerun()
            except Exception as e:
                st.error(f"Delete failed: {e}")

    def do_print() -> None:
        st.subheader("Print")
        if list_result.df.empty:
            st.info("Nothing to print")
            return
        st.dataframe(list_result.df, use_container_width=True, hide_index=True)
        csv = list_result.df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", data=csv, file_name=f"{form.TableName}.csv", mime="text/csv")

    # Add
    if actions[0].button("Add", type="primary"):
        if _dialog_supported():
            @st.dialog("Add record")
            def _dlg_add():
                do_add_dialog()

            _dlg_add()
        else:
            st.session_state["_inline_add"] = True

    # Edit
    if actions[1].button("Edit"):
        if selected_for_edit is None:
            st.warning("Select a record to edit")
        else:
            if _dialog_supported():
                @st.dialog("Edit record")
                def _dlg_edit():
                    do_edit_dialog(int(selected_for_edit))

                _dlg_edit()
            else:
                st.session_state["_inline_edit"] = int(selected_for_edit)

    # Delete
    if actions[2].button("Delete"):
        if not selected_for_delete:
            st.warning("Select record(s) to delete")
        else:
            if _dialog_supported():
                @st.dialog("Delete record(s)")
                def _dlg_del():
                    do_delete_dialog([int(x) for x in selected_for_delete])

                _dlg_del()
            else:
                st.session_state["_inline_delete"] = [int(x) for x in selected_for_delete]

    # Print
    if actions[3].button("Print"):
        do_print()

    # Fallback inline UIs if dialog isn't available
    if st.session_state.get("_inline_add"):
        with st.expander("Add record", expanded=True):
            do_add_dialog()
    if st.session_state.get("_inline_edit"):
        row_id = int(st.session_state.get("_inline_edit"))
        with st.expander(f"Edit record (Id={row_id})", expanded=True):
            do_edit_dialog(row_id)
    if st.session_state.get("_inline_delete"):
        row_ids = [int(x) for x in st.session_state.get("_inline_delete")]
        with st.expander("Confirm delete", expanded=True):
            do_delete_dialog(row_ids)


