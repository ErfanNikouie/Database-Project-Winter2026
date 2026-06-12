from __future__ import annotations

from sqlalchemy import select

from db.database import session_scope
from db.models import Form, FormField
from services.dynamic_table_service import DynamicTableService
from utils.naming import safe_identifier


class FormService:
    def list_forms(self) -> list[Form]:
        with session_scope() as session:
            return session.execute(select(Form).order_by(Form.Name)).scalars().all()

    def get_form(self, form_id: int) -> Form | None:
        with session_scope() as session:
            return session.get(Form, form_id)

    def get_form_with_fields(self, form_id: int) -> tuple[Form, list[FormField]] | None:
        with session_scope() as session:
            form = session.get(Form, form_id)
            if form is None:
                return None
            fields = session.execute(select(FormField).where(FormField.FormId == form_id).order_by(FormField.Id)).scalars().all()
            return form, fields

    def create_form(self, name: str, description: str | None, table_name: str) -> Form:
        safe_identifier(table_name, label="table name")
        with session_scope() as session:
            form = Form(Name=name.strip(), Description=(description or None), TableName=table_name.strip())
            session.add(form)
            session.flush()

        # Create the physical table immediately (at least with an Id column).
        # Columns will be added as fields are created.
        DynamicTableService().ensure_table(form, fields=[])
        return form

    def update_form(self, form_id: int, *, name: str, description: str | None, table_name: str) -> None:
        safe_identifier(table_name, label="table name")
        with session_scope() as session:
            form = session.get(Form, form_id)
            if form is None:
                raise ValueError("Form not found")
            form.Name = name.strip()
            form.Description = description or None
            form.TableName = table_name.strip()

    def delete_form(self, form_id: int) -> None:
        with session_scope() as session:
            form = session.get(Form, form_id)
            if form is None:
                return
            session.delete(form)

    def list_fields(self, form_id: int) -> list[FormField]:
        with session_scope() as session:
            return session.execute(
                select(FormField).where(FormField.FormId == form_id).order_by(FormField.Id)
            ).scalars().all()

    def create_field(
        self,
        form_id: int,
        field_name: str,
        field_type: str,
        mandatory: bool,
        lookup_id: int | None,
        target_table_name: str | None = None,
    ) -> FormField:
        safe_identifier(field_name, label="field name")
        with session_scope() as session:
            field = FormField(
                FormId=form_id,
                FieldName=field_name.strip(),
                FieldType=field_type.strip(),
                Mandatory=bool(mandatory),
                LookupId=lookup_id,
                TargetTableName=(target_table_name.strip() if target_table_name else None),
            )
            session.add(field)
            session.flush()

        # Sync physical table (add missing column)
        self.sync_form_table(form_id)
        return field

    def update_field(
        self,
        field_id: int,
        *,
        field_name: str,
        field_type: str,
        mandatory: bool,
        lookup_id: int | None,
        target_table_name: str | None = None,
    ) -> None:
        safe_identifier(field_name, label="field name")
        form_id: int | None = None
        with session_scope() as session:
            field = session.get(FormField, field_id)
            if field is None:
                raise ValueError("Field not found")
            field.FieldName = field_name.strip()
            field.FieldType = field_type.strip()
            field.Mandatory = bool(mandatory)
            field.LookupId = lookup_id
            field.TargetTableName = (target_table_name.strip() if target_table_name else None)

            form_id = int(field.FormId)

        # If the field was changed, ensure the physical table has the needed column.
        # (Renames are not supported; the old column will remain.)
        if form_id is not None:
            self.sync_form_table(form_id)

    def delete_field(self, field_id: int) -> None:
        with session_scope() as session:
            field = session.get(FormField, field_id)
            if field is None:
                return
            session.delete(field)

    def sync_form_table(self, form_id: int) -> None:
        """Create/sync the underlying SQLite table to match current fields."""
        with session_scope() as session:
            form = session.get(Form, form_id)
            if form is None:
                raise ValueError("Form not found")
            fields = session.execute(select(FormField).where(FormField.FormId == form_id)).scalars().all()

        DynamicTableService().ensure_table(form, fields)


