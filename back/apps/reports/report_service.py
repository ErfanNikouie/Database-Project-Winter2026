from __future__ import annotations

from sqlalchemy import MetaData, Table, func, inspect, select

from apps.common.db.sqlalchemy import get_engine
from apps.common.exceptions import ValidationException


class ReportService:
    @staticmethod
    def aggregate(table_name: str, group_by: str, metric_column: str, metric: str = "count") -> list[dict]:
        engine = get_engine()
        inspector = inspect(engine)
        if not inspector.has_table(table_name):
            raise ValidationException("Table does not exist")

        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=engine)

        if group_by not in table.c or metric_column not in table.c:
            raise ValidationException("Invalid report column")

        metric_functions = {
            "count": func.count(table.c[metric_column]),
            "sum": func.sum(table.c[metric_column]),
            "avg": func.avg(table.c[metric_column]),
            "min": func.min(table.c[metric_column]),
            "max": func.max(table.c[metric_column]),
        }
        if metric not in metric_functions:
            raise ValidationException("Unsupported metric")

        stmt = (
            select(table.c[group_by].label(group_by), metric_functions[metric].label("metric"))
            .group_by(table.c[group_by])
            .order_by(table.c[group_by])
        )
        with engine.begin() as connection:
            rows = connection.execute(stmt).mappings().all()
        return [dict(row) for row in rows]

