from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
from sqlalchemy import MetaData, Table, delete, insert, select, update
from sqlalchemy.engine import Engine
from sqlalchemy.exc import NoSuchTableError

from db.database import get_engine
from db.models import Form, FormField
from services.dynamic_table_service import DynamicTableService


@dataclass(frozen=True)
class ListResult:
    rows: list[dict[str, Any]]
    df: pd.DataFrame


class CrudService:
    """Generic CRUD for a dynamic table addressed by Form.TableName."""

    def __init__(self, engine: Engine | None = None):
        self.engine = engine or get_engine()

    def _reflect_table(self, table_name: str) -> Table:
        md = MetaData()
        try:
            return Table(table_name, md, autoload_with=self.engine)
        except NoSuchTableError as e:
            raise ValueError(f"Table '{table_name}' not found") from e

    def ensure_table_for_form(self, form: Form, fields: list[FormField]) -> None:
        DynamicTableService(self.engine).ensure_table(form, fields)

    def list_rows(self, table_name: str, *, limit: int = 500) -> ListResult:
        table = self._reflect_table(table_name)
        stmt = select(table).limit(limit)
        with self.engine.begin() as conn:
            result = conn.execute(stmt)
            rows = [dict(r._mapping) for r in result]
        df = pd.DataFrame(rows)
        return ListResult(rows=rows, df=df)

    def get_row(self, table_name: str, row_id: int) -> dict[str, Any] | None:
        table = self._reflect_table(table_name)
        if "Id" not in table.c:
            raise ValueError("Table does not have Id column")
        stmt = select(table).where(table.c.Id == row_id)
        with self.engine.begin() as conn:
            r = conn.execute(stmt).mappings().first()
        return dict(r) if r else None

    def insert_row(self, table_name: str, data: dict[str, Any]) -> int:
        table = self._reflect_table(table_name)
        data = {k: v for k, v in data.items() if k in table.c and k != "Id"}
        stmt = insert(table).values(**data)
        with self.engine.begin() as conn:
            result = conn.execute(stmt)
            pk = result.inserted_primary_key
            return int(pk[0]) if pk and pk[0] is not None else 0

    def update_row(self, table_name: str, row_id: int, data: dict[str, Any]) -> None:
        table = self._reflect_table(table_name)
        data = {k: v for k, v in data.items() if k in table.c and k != "Id"}
        stmt = update(table).where(table.c.Id == row_id).values(**data)
        with self.engine.begin() as conn:
            conn.execute(stmt)

    def delete_rows(self, table_name: str, row_ids: list[int]) -> None:
        if not row_ids:
            return
        table = self._reflect_table(table_name)
        stmt = delete(table).where(table.c.Id.in_(row_ids))
        with self.engine.begin() as conn:
            conn.execute(stmt)

