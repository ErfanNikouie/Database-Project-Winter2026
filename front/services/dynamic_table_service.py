from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sqlalchemy import (
    Boolean,
    Column,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    inspect,
    text,
)
from sqlalchemy.engine import Engine
from sqlalchemy.types import TypeEngine

from db.database import get_engine
from db.models import Form, FormField
from utils.naming import safe_identifier


@dataclass(frozen=True)
class FieldTypeMapping:
    sqlalchemy_type: TypeEngine
    sqlite_decl: str


_FIELD_TYPE_MAP: dict[str, FieldTypeMapping] = {
    "text": FieldTypeMapping(Text(), "TEXT"),
    "number": FieldTypeMapping(Float(), "REAL"),
    "integer": FieldTypeMapping(Integer(), "INTEGER"),
    "date": FieldTypeMapping(String(30), "TEXT"),  # ISO strings
    "lookup": FieldTypeMapping(Integer(), "INTEGER"),
    "foreign_key": FieldTypeMapping(Integer(), "INTEGER"),
    "bool": FieldTypeMapping(Boolean(), "INTEGER"),
}


class DynamicTableService:
    """Create/sync dynamic tables that are defined by Form + FormField metadata.

    Supports:
    - Create table if missing
    - Add missing columns if fields were added (additive schema evolution)

    Note: dropping/renaming columns is intentionally not supported in this prototype.
    """

    def __init__(self, engine: Engine | None = None):
        self.engine = engine or get_engine()

    def validate_form_identifiers(self, form: Form) -> None:
        safe_identifier(form.TableName, label="table name")

    def _column_for_field(self, field: FormField) -> Column:
        field_name = safe_identifier(field.FieldName, label="field name")
        mapping = _FIELD_TYPE_MAP.get(field.FieldType)
        if mapping is None:
            raise ValueError(
                f"Unsupported FieldType '{field.FieldType}' for field '{field.FieldName}'. "
                f"Supported: {', '.join(sorted(_FIELD_TYPE_MAP.keys()))}"
            )
        # Nullable is inverse of Mandatory
        return Column(field_name, mapping.sqlalchemy_type, nullable=not bool(field.Mandatory))

    def build_table(self, form: Form, fields: Iterable[FormField]) -> Table:
        self.validate_form_identifiers(form)
        md = MetaData()

        columns: list[Column] = [Column("Id", Integer(), primary_key=True, autoincrement=True)]
        for f in fields:
            if f.FieldName.strip() == "Id":
                continue
            columns.append(self._column_for_field(f))

        return Table(form.TableName, md, *columns)

    def ensure_table(self, form: Form, fields: Iterable[FormField]) -> None:
        """Idempotently create/sync the physical table for the given form."""
        table_name = safe_identifier(form.TableName, label="table name")
        inspector = inspect(self.engine)
        existing_tables = set(inspector.get_table_names())

        if table_name not in existing_tables:
            table = self.build_table(form, fields)
            table.metadata.create_all(self.engine, tables=[table])
            return

        # Add missing columns (SQLite supports ADD COLUMN)
        existing_cols = {c["name"] for c in inspector.get_columns(table_name)}
        for f in fields:
            col_name = safe_identifier(f.FieldName, label="field name")
            if col_name == "Id":
                continue
            if col_name in existing_cols:
                continue

            mapping = _FIELD_TYPE_MAP.get(f.FieldType)
            if mapping is None:
                continue

            # IMPORTANT (robustness): when evolving an existing table, avoid NOT NULL.
            # SQLite will fail to add a NOT NULL column if existing rows would violate it
            # (unless a DEFAULT is provided). For this prototype we enforce Mandatory via UI.
            ddl = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {mapping.sqlite_decl}"
            with self.engine.begin() as conn:
                conn.execute(text(ddl))



