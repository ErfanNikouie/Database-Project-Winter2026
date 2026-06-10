from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import MetaData, Table, func, inspect, select

from apps.common.db.sqlalchemy import get_engine
from apps.common.exceptions import NotFoundException, ValidationException
from apps.forms.models import Form, FormField
from apps.lookups.models import LookupValue


class ValidationService:
    @staticmethod
    def get_form_or_raise(table_name: str) -> Form:
        form = Form.objects.filter(table_name=table_name).first()
        if not form:
            raise NotFoundException(f"Unknown table: {table_name}")
        return form

    @staticmethod
    def get_form_fields_map(form: Form) -> dict[str, FormField]:
        return {field.name: field for field in form.fields.all()}

    @classmethod
    def validate_payload(cls, form: Form, payload: dict, is_update: bool = False) -> None:
        fields_map = cls.get_form_fields_map(form)
        server_managed_fields = {"id", "created_at", "updated_at", "password_hash"}
        allowed_columns = set(fields_map.keys()) | {"id", "created_at", "updated_at", "password"}
        for column in payload.keys():
            if column not in allowed_columns:
                raise ValidationException("Column is not defined in metadata", field=column)

        if not is_update:
            for field in fields_map.values():
                if field.name in server_managed_fields:
                    continue
                if field.mandatory and field.name not in payload:
                    raise ValidationException("Field is required", field=field.name)

        for key, value in payload.items():
            if key in {"id", "created_at", "updated_at"}:
                continue
            form_field = fields_map.get(key)
            if not form_field:
                continue
            cls._validate_value_type(form_field, value)
            cls._validate_lookup(form_field, value)
            cls._validate_foreign_key(form_field, value)

        cls._validate_unique_constraints(form, fields_map, payload, is_update)

    @staticmethod
    def _validate_value_type(field: FormField, value) -> None:
        if value is None:
            if field.mandatory:
                raise ValidationException("Field cannot be null", field=field.name)
            return

        type_checkers = {
            "Integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
            "Double": lambda v: isinstance(v, (int, float, Decimal)) and not isinstance(v, bool),
            "Decimal": lambda v: isinstance(v, (int, float, Decimal)) and not isinstance(v, bool),
            "String": lambda v: isinstance(v, str),
            "Text": lambda v: isinstance(v, str),
            "Date": lambda v: isinstance(v, str) and _is_iso_date(v),
            "DateTime": lambda v: isinstance(v, str) and _is_iso_datetime(v),
            "Boolean": lambda v: isinstance(v, bool),
            "Lookup": lambda v: isinstance(v, int),
            "ForeignKey": lambda v: isinstance(v, int),
        }

        checker = type_checkers[field.type]
        if not checker(value):
            raise ValidationException("Invalid data type", field=field.name)

    @staticmethod
    def _validate_lookup(field: FormField, value) -> None:
        if field.type != "Lookup" or value is None:
            return
        if field.lookup_id is None:
            raise ValidationException("Lookup configuration is missing", field=field.name)
        exists = LookupValue.objects.filter(id=value, lookup_id=field.lookup_id).exists()
        if not exists:
            raise ValidationException("Lookup value is not valid", field=field.name)

    @staticmethod
    def _validate_foreign_key(field: FormField, value) -> None:
        if field.type != "ForeignKey" or value is None:
            return
        if not field.foreign_key_table:
            raise ValidationException("Foreign key table is missing", field=field.name)

        engine = get_engine()
        inspector = inspect(engine)
        fk_table_name = field.foreign_key_table
        fk_column = field.foreign_key_field or "id"
        if not inspector.has_table(fk_table_name):
            raise ValidationException("Foreign key table does not exist", field=field.name)

        metadata = MetaData()
        fk_table = Table(fk_table_name, metadata, autoload_with=engine)
        if fk_column not in fk_table.c:
            raise ValidationException("Foreign key column does not exist", field=field.name)

        with engine.begin() as connection:
            exists = connection.execute(
                select(func.count()).select_from(fk_table).where(fk_table.c[fk_column] == value)
            ).scalar_one()
        if not exists:
            raise ValidationException("Referenced record does not exist", field=field.name)

    @staticmethod
    def _validate_unique_constraints(form: Form, fields_map: dict[str, FormField], payload: dict, is_update: bool) -> None:
        unique_fields = [field for field in fields_map.values() if field.unique and field.name in payload]
        if not unique_fields:
            return

        engine = get_engine()
        inspector = inspect(engine)
        if not inspector.has_table(form.table_name):
            return

        metadata = MetaData()
        table = Table(form.table_name, metadata, autoload_with=engine)
        record_id = payload.get("id") if is_update else None

        with engine.begin() as connection:
            for field in unique_fields:
                query = select(func.count()).select_from(table).where(table.c[field.name] == payload[field.name])
                if record_id:
                    query = query.where(table.c.id != record_id)
                count = connection.execute(query).scalar_one()
                if count:
                    raise ValidationException("Value must be unique", field=field.name)


def _is_iso_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def _is_iso_datetime(value: str) -> bool:
    try:
        datetime.fromisoformat(value)
        return True
    except ValueError:
        return False



