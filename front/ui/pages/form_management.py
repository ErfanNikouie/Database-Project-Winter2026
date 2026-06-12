from __future__ import annotations

import streamlit as st
from sqlalchemy import inspect

from db.database import get_engine

from services.form_service import FormService
from services.lookup_service import LookupService


SUPPORTED_FIELD_TYPES = ["text", "number", "integer", "date", "lookup", "foreign_key", "bool"]


def render_form_management() -> None:
    st.title("Form Management")

    fs = FormService()
    ls = LookupService()

    forms = fs.list_forms()
    form_options = {f"{f.Name} (#{f.Id}, {f.TableName})": f.Id for f in forms}

    selected_form_id = st.selectbox("Select form", options=[None] + list(form_options.values()), format_func=lambda x: "(new / none)" if x is None else next(k for k, v in form_options.items() if v == x))

    st.divider()
    st.subheader("Create / Edit Form")

    current = fs.get_form(selected_form_id) if selected_form_id else None

    with st.form("form_edit"):
        name = st.text_input("Name", value=current.Name if current else "")
        description = st.text_area("Description", value=current.Description if current and current.Description else "")
        table_name = st.text_input("TableName", value=current.TableName if current else "")

        col1, col2, col3 = st.columns([1, 1, 1])
        save = col1.form_submit_button("Save", type="primary")
        delete = col2.form_submit_button("Delete")
        sync = col3.form_submit_button("Sync Table")

    if save:
        try:
            if not name.strip() or not table_name.strip():
                st.error("Name and TableName are required")
            else:
                if current is None:
                    created = fs.create_form(name=name, description=description, table_name=table_name)
                    st.success(f"Created form #{created.Id}")
                else:
                    fs.update_form(current.Id, name=name, description=description, table_name=table_name)
                    st.success("Updated")
                st.rerun()
        except Exception as e:
            st.error(f"Save failed: {e}")

    if delete:
        if current is None:
            st.warning("Select a form to delete")
        else:
            try:
                fs.delete_form(current.Id)
                st.success("Deleted")
                st.rerun()
            except Exception as e:
                st.error(f"Delete failed: {e}")

    if sync:
        if current is None:
            st.warning("Select a form")
        else:
            try:
                fs.sync_form_table(current.Id)
                st.success("Table synced")
            except Exception as e:
                st.error(f"Sync failed: {e}")

    if current is None:
        st.info("Select a form to manage its fields.")
        return

    st.divider()
    st.subheader("Form Fields")

    fields = fs.list_fields(current.Id)
    if fields:
        st.dataframe(
            [{
                "Id": f.Id,
                "FieldName": f.FieldName,
                "FieldType": f.FieldType,
                "Mandatory": f.Mandatory,
                "LookupId": f.LookupId,
            } for f in fields],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No fields yet.")

    field_map = {f"{f.FieldName} (#{f.Id})": f.Id for f in fields}
    selected_field_id = st.selectbox(
        "Select field",
        options=[None] + list(field_map.values()),
        format_func=lambda x: "(new)" if x is None else next(k for k, v in field_map.items() if v == x),
    )

    current_field = next((f for f in fields if f.Id == selected_field_id), None)

    lookups = ls.list_lookups()
    lookup_options = {"(none)": None}
    for l in lookups:
        lookup_options[f"{(l.Name or l.Description)} (#{l.Id})"] = l.Id

    # Target table options for foreign keys
    insp = inspect(get_engine())
    all_tables = [t for t in insp.get_table_names() if t != "sqlite_sequence"]
    # Hide metadata tables by default but still allow selecting them if needed
    hidden_prefixes = {"sqlite_"}
    target_table_options = [None] + sorted(all_tables)

    with st.form("field_edit"):
        field_name = st.text_input("FieldName", value=current_field.FieldName if current_field else "")
        field_type = st.selectbox(
            "FieldType",
            options=SUPPORTED_FIELD_TYPES,
            index=SUPPORTED_FIELD_TYPES.index(str(current_field.FieldType))
            if current_field and str(current_field.FieldType) in SUPPORTED_FIELD_TYPES
            else 0,
        )
        mandatory = st.checkbox("Mandatory", value=bool(current_field.Mandatory) if current_field else False)

        lookup_id = None
        target_table_name = None
        if field_type == "lookup":
            lookup_id = st.selectbox(
                "Lookup",
                options=list(lookup_options.values()),
                format_func=lambda x: next(k for k, v in lookup_options.items() if v == x),
                index=list(lookup_options.values()).index(int(current_field.LookupId))
                if current_field and current_field.LookupId is not None and int(current_field.LookupId) in lookup_options.values()
                else 0,
            )
        elif field_type == "foreign_key":
            target_table_name = st.selectbox(
                "Target Table",
                options=target_table_options,
                index=target_table_options.index(str(current_field.TargetTableName))
                if current_field and current_field.TargetTableName and str(current_field.TargetTableName) in target_table_options
                else 0,
                help="Records will be loaded from this table and shown as a dropdown in the form.",
            )
        else:
            st.caption("Lookup/TargetTable is only applicable for FieldType=lookup or foreign_key")

        col1, col2, col3 = st.columns([1, 1, 1])
        save_f = col1.form_submit_button("Save Field", type="primary")
        delete_f = col2.form_submit_button("Delete Field")
        sync2 = col3.form_submit_button("Sync Table")

    if save_f:
        try:
            if not field_name.strip():
                st.error("FieldName is required")
            else:
                if current_field is None:
                    fs.create_field(
                        current.Id,
                        field_name=field_name,
                        field_type=field_type,
                        mandatory=mandatory,
                        lookup_id=lookup_id,
                        target_table_name=target_table_name,
                    )
                    st.success("Field created")
                else:
                    fs.update_field(
                        current_field.Id,
                        field_name=field_name,
                        field_type=field_type,
                        mandatory=mandatory,
                        lookup_id=lookup_id,
                        target_table_name=target_table_name,
                    )
                    st.success("Field updated")
                st.rerun()
        except Exception as e:
            st.error(f"Save field failed: {e}")

    if delete_f:
        if current_field is None:
            st.warning("Select a field")
        else:
            try:
                fs.delete_field(current_field.Id)
                st.success("Field deleted")
                st.rerun()
            except Exception as e:
                st.error(f"Delete field failed: {e}")

    if sync2:
        try:
            fs.sync_form_table(current.Id)
            st.success("Table synced")
        except Exception as e:
            st.error(f"Sync failed: {e}")

