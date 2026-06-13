from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import re
from typing import Any

from sqlalchemy import MetaData, Table, and_, func, inspect, select

from apps.common.db.sqlalchemy import get_engine
from apps.common.exceptions import PermissionDeniedException, ValidationException
from apps.common.permissions.permission_service import PermissionService
from apps.forms.models import Form, FormField
from apps.forms.services.filter_parser import FilterParser
from apps.reports.models import Report, ReportField


@dataclass(frozen=True)
class ReportColumn:
    key: str
    name: str
    form_table: str
    field_name: str
    field_type: str


def _normalize_key(raw: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_]+", "_", raw.strip().lower())
    value = value.strip("_")
    return value or "column"


class DynamicReportService:
    @classmethod
    def list_available_reports(cls, *, user) -> list[dict[str, Any]]:
        reports = Report.objects.select_related("base_form").prefetch_related(
            "fields__form", "fields__form_field"
        )
        available: list[dict[str, Any]] = []
        for report in reports:
            if not cls._can_list_table(user, report.base_form.table_name):
                continue
            if not cls._visible_report_fields(user=user, report=report):
                continue
            available.append(
                {
                    "id": int(report.id),
                    "name": report.name,
                    "description": report.description,
                }
            )
        return available

    @classmethod
    def run_report(
        cls,
        *,
        user,
        report_id: int,
        filters: dict[str, Any],
        sort_by: str | None,
        sort_direction: str,
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        report = (
            Report.objects.select_related("base_form")
            .prefetch_related("fields__form", "fields__form_field")
            .filter(id=report_id)
            .first()
        )
        if not report:
            raise ValidationException("Report does not exist", field="report_id")

        base_form = report.base_form
        if not cls._can_list_table(user, base_form.table_name):
            raise PermissionDeniedException("User is not authorized for this operation")

        visible_fields = cls._visible_report_fields(user=user, report=report)
        if not visible_fields:
            raise PermissionDeniedException("No accessible fields for this report")

        engine = get_engine()
        relationship_graph = cls._build_relationship_graph()

        join_paths_by_table: dict[str, list[dict[str, str]]] = {}
        required_tables = {base_form.table_name, *{f.form.table_name for f in visible_fields}}
        for report_field in visible_fields:
            target_table = report_field.form.table_name
            if target_table == base_form.table_name:
                join_paths_by_table[target_table] = []
                continue
            join_path = cls._find_join_path(
                graph=relationship_graph,
                base_table=base_form.table_name,
                target_table=target_table,
            )
            if not join_path:
                raise ValidationException(
                    "No join path exists between base form and referenced form",
                    field=report_field.form.table_name,
                )
            join_paths_by_table[target_table] = join_path
            for edge in join_path:
                required_tables.add(edge["source_table"])
                required_tables.add(edge["target_table"])
                required_tables.add(edge["next_table"])

        tables = cls._reflect_tables(list(required_tables))

        from_clause = tables[base_form.table_name]
        joined_tables = {base_form.table_name}
        for report_field in visible_fields:
            target_table = report_field.form.table_name
            if target_table in joined_tables:
                continue
            join_path = join_paths_by_table.get(target_table, [])

            for edge in join_path:
                next_table = edge["next_table"]
                if next_table in joined_tables:
                    continue
                join_condition = (
                    tables[edge["source_table"]].c[edge["source_column"]]
                    == tables[edge["target_table"]].c[edge["target_column"]]
                )
                from_clause = from_clause.join(tables[next_table], join_condition)
                joined_tables.add(next_table)

        selected_columns: list[ReportColumn] = []
        select_exprs = []
        used_keys: set[str] = set()
        key_to_column: dict[str, tuple[ReportColumn, Any]] = {}
        fallback_key_map: dict[str, str] = {}

        for report_field in sorted(visible_fields, key=lambda item: (item.display_order, item.id)):
            field_name = report_field.form_field.name
            table_name = report_field.form.table_name
            if field_name not in tables[table_name].c:
                raise ValidationException("Referenced form field does not exist physically", field=field_name)
            raw_name = report_field.display_name or field_name
            column_key = _normalize_key(raw_name)
            while column_key in used_keys:
                column_key = f"{column_key}_{report_field.id}"
            used_keys.add(column_key)

            report_column = ReportColumn(
                key=column_key,
                name=raw_name,
                form_table=table_name,
                field_name=field_name,
                field_type=report_field.form_field.type,
            )
            selected_columns.append(report_column)
            expr = tables[table_name].c[field_name]
            select_exprs.append(expr.label(column_key))
            key_to_column[column_key] = (report_column, expr)
            if field_name not in fallback_key_map:
                fallback_key_map[field_name] = column_key

        if not selected_columns:
            raise ValidationException("Report has no selectable fields")

        predicates = []
        for filter_key, expression in (filters or {}).items():
            resolved_key = filter_key if filter_key in key_to_column else fallback_key_map.get(filter_key)
            if not resolved_key:
                raise ValidationException("Unknown filter field", field=filter_key)
            report_column, expr = key_to_column[resolved_key]
            predicate = FilterParser.parse(
                report_column.key,
                report_column.field_type,
                str(expression),
                expr,
            )
            if predicate is not None:
                predicates.append(predicate)

        sort_key = sort_by or selected_columns[0].key
        resolved_sort_key = sort_key if sort_key in key_to_column else fallback_key_map.get(sort_key)
        if not resolved_sort_key:
            raise ValidationException("Invalid sort column", field="sort_by")
        _, sort_expr = key_to_column[resolved_sort_key]
        order_expr = sort_expr.desc() if sort_direction == "desc" else sort_expr.asc()

        result_query = select(*select_exprs).select_from(from_clause)
        count_query = select(func.count()).select_from(from_clause)
        if predicates:
            combined = and_(*predicates)
            result_query = result_query.where(combined)
            count_query = count_query.where(combined)

        result_query = result_query.order_by(order_expr).limit(limit).offset(offset)

        with engine.begin() as connection:
            total = int(connection.execute(count_query).scalar_one())
            rows = [dict(row) for row in connection.execute(result_query).mappings().all()]

        return {
            "count": total,
            "columns": [
                {
                    "key": column.key,
                    "name": column.name,
                    "form_table": column.form_table,
                    "field_name": column.field_name,
                }
                for column in selected_columns
            ],
            "rows": rows,
        }

    @staticmethod
    def _can_list_table(user, table_name: str) -> bool:
        try:
            PermissionService.assert_table_permission(user, table_name, "list")
            return True
        except PermissionDeniedException:
            return False

    @classmethod
    def _visible_report_fields(cls, *, user, report: Report) -> list[ReportField]:
        visible: list[ReportField] = []
        for report_field in report.fields.all():
            if not report_field.form_id or not report_field.form_field_id:
                continue
            if report_field.form_field.form_id != report_field.form_id:
                continue
            if not cls._can_list_table(user, report_field.form.table_name):
                continue
            visible.append(report_field)
        return visible

    @staticmethod
    def _reflect_tables(table_names: list[str]) -> dict[str, Table]:
        engine = get_engine()
        inspector = inspect(engine)
        metadata = MetaData()
        tables: dict[str, Table] = {}
        for table_name in sorted(set(table_names)):
            if not inspector.has_table(table_name):
                raise ValidationException("Referenced form table does not exist", field=table_name)
            tables[table_name] = Table(table_name, metadata, autoload_with=engine)
        return tables

    @staticmethod
    def _build_relationship_graph() -> dict[str, list[dict[str, str]]]:
        forms_by_table = {form.table_name: form for form in Form.objects.all()}
        graph: dict[str, list[dict[str, str]]] = {table_name: [] for table_name in forms_by_table.keys()}

        fk_fields = FormField.objects.filter(type="ForeignKey").exclude(foreign_key_table="")
        for field in fk_fields:
            source_table = field.form.table_name
            target_table = field.foreign_key_table
            target_column = field.foreign_key_field or "id"
            if target_table not in forms_by_table:
                continue

            graph.setdefault(source_table, []).append(
                {
                    "next_table": target_table,
                    "source_table": source_table,
                    "source_column": field.name,
                    "target_table": target_table,
                    "target_column": target_column,
                }
            )
            graph.setdefault(target_table, []).append(
                {
                    "next_table": source_table,
                    "source_table": source_table,
                    "source_column": field.name,
                    "target_table": target_table,
                    "target_column": target_column,
                }
            )

        return graph

    @staticmethod
    def _find_join_path(
        *,
        graph: dict[str, list[dict[str, str]]],
        base_table: str,
        target_table: str,
    ) -> list[dict[str, str]]:
        if base_table == target_table:
            return []

        visited = {base_table}
        queue: deque[tuple[str, list[dict[str, str]]]] = deque([(base_table, [])])
        while queue:
            current, path = queue.popleft()
            for edge in graph.get(current, []):
                next_table = edge["next_table"]
                if next_table in visited:
                    continue
                next_path = [*path, edge]
                if next_table == target_table:
                    return next_path
                visited.add(next_table)
                queue.append((next_table, next_path))
        return []


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

