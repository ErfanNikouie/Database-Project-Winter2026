from __future__ import annotations

import re
from decimal import Decimal

from sqlalchemy import (
    BIGINT,
    BOOLEAN,
    DATE,
    DateTime,
    DECIMAL,
    FLOAT,
    INTEGER,
    TEXT,
    VARCHAR,
    Column,
    ForeignKey,
    MetaData,
    Table,
    inspect,
    text,
)

from apps.common.db.sqlalchemy import get_engine
from apps.common.exceptions import ValidationException
from apps.forms.models import Form, FormField


IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class SchemaService:
    @staticmethod
    def ensure_safe_identifier(identifier: str) -> str:
        if not IDENTIFIER_RE.match(identifier):
            raise ValidationException("Invalid identifier")
        return identifier

    @classmethod
    def create_dynamic_table(cls, form: Form) -> None:
        if form.is_system:
            return

        table_name = cls.ensure_safe_identifier(form.table_name)
        engine = get_engine()
        inspector = inspect(engine)
        if inspector.has_table(table_name):
            return

        columns = [
            Column("id", BIGINT, primary_key=True, autoincrement=True),
            Column("created_at", DateTime(), nullable=False, server_default=text("CURRENT_TIMESTAMP")),
            Column("updated_at", DateTime(), nullable=False, server_default=text("CURRENT_TIMESTAMP")),
        ]

        for field in form.fields.order_by("sort_order", "id"):
            columns.append(cls._column_from_field(field))

        metadata = MetaData()
        table = Table(table_name, metadata, *columns)
        metadata.create_all(engine, tables=[table])

    @classmethod
    def add_field(cls, form: Form, field: FormField) -> None:
        if form.is_system:
            return
        table_name = cls.ensure_safe_identifier(form.table_name)
        column_name = cls.ensure_safe_identifier(field.name)
        column = cls._column_from_field(field)
        engine = get_engine()
        nullable = "NOT NULL" if not column.nullable else ""
        unique = "UNIQUE" if field.unique else ""
        default_sql = f"DEFAULT {cls._format_default(field.default_value)}" if field.default_value else ""
        sql = (
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} "
            f"{cls._sql_type(field.type)} {nullable} {unique} {default_sql}"
        ).strip()
        with engine.begin() as connection:
            connection.execute(text(sql))
            if field.type == "ForeignKey" and field.foreign_key_table:
                fk_table = cls.ensure_safe_identifier(field.foreign_key_table)
                fk_field = cls.ensure_safe_identifier(field.foreign_key_field or "id")
                constraint = f"fk_{table_name}_{column_name}_{fk_table}_{fk_field}"
                connection.execute(
                    text(
                        f"ALTER TABLE {table_name} "
                        f"ADD CONSTRAINT {constraint} FOREIGN KEY ({column_name}) REFERENCES {fk_table} ({fk_field})"
                    )
                )

    @classmethod
    def update_field(cls, form: Form, before: FormField, after: FormField) -> None:
        if form.is_system:
            return
        table_name = cls.ensure_safe_identifier(form.table_name)
        column_name = cls.ensure_safe_identifier(after.name)
        engine = get_engine()
        with engine.begin() as connection:
            if before.type != after.type:
                connection.execute(
                    text(
                        f"ALTER TABLE {table_name} ALTER COLUMN {column_name} "
                        f"TYPE {cls._sql_type(after.type)}"
                    )
                )
            if before.mandatory != after.mandatory:
                clause = "SET NOT NULL" if after.mandatory else "DROP NOT NULL"
                connection.execute(text(f"ALTER TABLE {table_name} ALTER COLUMN {column_name} {clause}"))

    @classmethod
    def drop_field(cls, form: Form, field_name: str) -> None:
        if form.is_system:
            return
        table_name = cls.ensure_safe_identifier(form.table_name)
        field_name = cls.ensure_safe_identifier(field_name)
        engine = get_engine()
        with engine.begin() as connection:
            connection.execute(text(f"ALTER TABLE {table_name} DROP COLUMN IF EXISTS {field_name} CASCADE"))

    @classmethod
    def drop_dynamic_table(cls, form: Form) -> None:
        if form.is_system:
            raise ValidationException("System forms cannot be deleted")
        table_name = cls.ensure_safe_identifier(form.table_name)
        engine = get_engine()
        with engine.begin() as connection:
            connection.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))

    @classmethod
    def _column_from_field(cls, field: FormField) -> Column:
        column_name = cls.ensure_safe_identifier(field.name)
        kwargs = {"nullable": not field.mandatory, "unique": field.unique}
        if field.default_value:
            kwargs["default"] = cls._parse_default(field.default_value, field.type)

        if field.type == "ForeignKey" and field.foreign_key_table:
            foreign_table = cls.ensure_safe_identifier(field.foreign_key_table)
            foreign_field = cls.ensure_safe_identifier(field.foreign_key_field or "id")
            return Column(column_name, BIGINT, ForeignKey(f"{foreign_table}.{foreign_field}"), **kwargs)

        if field.type == "Lookup":
            return Column(column_name, BIGINT, **kwargs)
        return Column(column_name, cls._sa_type(field.type), **kwargs)

    @staticmethod
    def _sa_type(field_type: str):
        return {
            "Integer": INTEGER,
            "Double": FLOAT,
            "Decimal": DECIMAL(18, 4),
            "String": VARCHAR(255),
            "Text": TEXT,
            "Date": DATE,
            "DateTime": DateTime(),
            "Boolean": BOOLEAN,
            "Lookup": BIGINT,
            "ForeignKey": BIGINT,
        }[field_type]

    @staticmethod
    def _sql_type(field_type: str) -> str:
        return {
            "Integer": "INTEGER",
            "Double": "DOUBLE PRECISION",
            "Decimal": "NUMERIC(18,4)",
            "String": "VARCHAR(255)",
            "Text": "TEXT",
            "Date": "DATE",
            "DateTime": "TIMESTAMP",
            "Boolean": "BOOLEAN",
            "Lookup": "BIGINT",
            "ForeignKey": "BIGINT",
        }[field_type]

    @staticmethod
    def _parse_default(raw: str, field_type: str):
        if field_type in {"Integer", "Lookup", "ForeignKey"}:
            return int(raw)
        if field_type in {"Double", "Decimal"}:
            return Decimal(raw)
        if field_type == "Boolean":
            return raw.lower() in {"1", "true", "yes"}
        return raw

    @staticmethod
    def _format_default(raw: str):
        try:
            float(raw)
            return raw
        except ValueError:
            if raw.lower() in {"true", "false"}:
                return raw.upper()
            escaped = raw.replace("'", "''")
            return f"'{escaped}'"


