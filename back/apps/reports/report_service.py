from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from functools import lru_cache
import re
from typing import Any

from sqlalchemy import MetaData, Table, and_, exists, func, inspect, literal, select

from apps.common.db.sqlalchemy import get_engine
from apps.common.exceptions import PermissionDeniedException, ValidationException
from apps.common.permissions.permission_service import PermissionService
from apps.forms.models import Form, FormField
from apps.forms.services.filter_parser import FilterParser
from apps.reports.models import (
    Report,
    ReportAggregationType,
    ReportExpressionType,
    ReportField,
    ReportSortDirection,
)


@dataclass(frozen=True)
class ReportColumn:
    key: str
    name: str
    form_table: str
    field_name: str
    field_type: str
    lookup_id: int | None = None
    foreign_key_table: str = ""
    foreign_key_field: str = "id"
    expression_type: str = ReportExpressionType.DIRECT
    aggregation_type: str = ReportAggregationType.NONE
    group_by_flag: bool = False


@dataclass(frozen=True)
class ResolvedFieldRef:
    form: Form
    field: FormField


def _normalize_key(raw: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_]+", "_", raw.strip().lower())
    value = value.strip("_")
    return value or "column"


class DynamicReportService:
    _join_path_cache: dict[tuple[str, str], list[dict[str, str]]] = {}

    @classmethod
    def get_report_definition(cls, *, user, report_id: int) -> dict[str, Any]:
        report = cls._load_report(report_id=report_id)
        cls._assert_user_can_access_report(user=user, report=report)

        visible_fields = cls._visible_report_fields(user=user, report=report)
        if not visible_fields:
            raise PermissionDeniedException("No accessible fields for this report")

        columns = cls._build_report_columns(base_form=report.base_form, visible_fields=visible_fields)
        return {
            "report_id": int(report.id),
            "name": report.name,
            "description": report.description,
            "fields": [
                {
                    "key": column.key,
                    "name": column.name,
                    "type": column.field_type,
                    "form_table": column.form_table,
                    "field_name": column.field_name,
                    "lookup_id": column.lookup_id,
                    "foreign_key_table": column.foreign_key_table,
                    "foreign_key_field": column.foreign_key_field,
                    "expression_type": column.expression_type,
                    "aggregation_type": column.aggregation_type,
                    "group_by_flag": column.group_by_flag,
                }
                for column in columns
            ],
        }

    @classmethod
    def list_available_reports(cls, *, user) -> list[dict[str, Any]]:
        reports = Report.objects.select_related("base_form").prefetch_related(
            "fields__form",
            "fields__form_field__form",
            "fields__target_field__form",
            "fields__related_form",
            "fields__sort_field__form",
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
        report = cls._load_report(report_id=report_id)
        cls._assert_user_can_access_report(user=user, report=report)

        visible_fields = cls._visible_report_fields(user=user, report=report)
        if not visible_fields:
            raise PermissionDeniedException("No accessible fields for this report")

        base_form = report.base_form
        selected_columns = cls._build_report_columns(base_form=base_form, visible_fields=visible_fields)
        has_base_id_column = any(
            column.form_table == base_form.table_name and column.field_name == "id"
            for column in selected_columns
        )
        if not has_base_id_column:
            selected_columns = [
                *selected_columns,
                ReportColumn(
                    key="id",
                    name="Id",
                    form_table=base_form.table_name,
                    field_name="id",
                    field_type="Integer",
                    expression_type=ReportExpressionType.DIRECT,
                    aggregation_type=ReportAggregationType.NONE,
                    group_by_flag=False,
                ),
            ]
        if not selected_columns:
            raise ValidationException("Report has no selectable fields")

        relationship_graph = cls._build_relationship_graph()
        required_tables = {base_form.table_name}
        join_paths: dict[str, list[dict[str, str]]] = {}

        grouped_mode = any(
            column.group_by_flag or column.expression_type == ReportExpressionType.GROUPED_AGGREGATE
            for column in selected_columns
        )

        for report_field in visible_fields:
            for form in cls._forms_touched_by_field(base_form=base_form, report_field=report_field):
                required_tables.add(form.table_name)
                if form.table_name == base_form.table_name:
                    continue
                path = cls._find_join_path(
                    graph=relationship_graph,
                    base_table=base_form.table_name,
                    target_table=form.table_name,
                )
                if not path:
                    raise ValidationException(
                        "No join path exists between base form and referenced form",
                        field=form.table_name,
                    )
                join_paths[form.table_name] = path
                for edge in path:
                    required_tables.add(edge["source_table"])
                    required_tables.add(edge["target_table"])

        tables = cls._reflect_tables(tuple(sorted(required_tables)))
        base_table = tables[base_form.table_name]

        from_clause = base_table
        joined_tables = {base_form.table_name}

        for column in selected_columns:
            if column.expression_type in {
                ReportExpressionType.AGGREGATE,
                ReportExpressionType.LATEST,
                ReportExpressionType.EXISTS,
            }:
                continue
            if column.form_table == base_form.table_name:
                continue
            if column.form_table not in join_paths:
                continue
            from_clause, joined_tables = cls._apply_join_path(
                from_clause=from_clause,
                joined_tables=joined_tables,
                tables=tables,
                path=join_paths[column.form_table],
            )

        if grouped_mode:
            for report_field in visible_fields:
                if report_field.expression_type != ReportExpressionType.GROUPED_AGGREGATE:
                    continue
                related_form = report_field.related_form or report_field.form
                if not related_form or related_form.table_name == base_form.table_name:
                    continue
                path = join_paths.get(related_form.table_name, [])
                from_clause, joined_tables = cls._apply_join_path(
                    from_clause=from_clause,
                    joined_tables=joined_tables,
                    tables=tables,
                    path=path,
                )

        select_exprs: list[Any] = []
        group_by_exprs: list[Any] = []
        key_to_column: dict[str, tuple[ReportColumn, Any]] = {}
        fallback_key_map: dict[str, str] = {}

        for report_field, report_column in zip(visible_fields, selected_columns):
            expr = cls._build_column_expression(
                base_form=base_form,
                report_field=report_field,
                report_column=report_column,
                tables=tables,
                join_paths=join_paths,
                grouped_mode=grouped_mode,
            )
            select_exprs.append(expr.label(report_column.key))
            key_to_column[report_column.key] = (report_column, expr)
            if report_column.field_name and report_column.field_name not in fallback_key_map:
                fallback_key_map[report_column.field_name] = report_column.key
            if report_column.group_by_flag:
                group_by_exprs.append(expr)

        if len(selected_columns) > len(visible_fields):
            for extra_column in selected_columns[len(visible_fields) :]:
                if extra_column.form_table != base_form.table_name or extra_column.field_name != "id":
                    continue
                expr = tables[base_form.table_name].c.id
                select_exprs.append(expr.label(extra_column.key))
                key_to_column[extra_column.key] = (extra_column, expr)
                fallback_key_map.setdefault("id", extra_column.key)

        predicates: list[Any] = []
        metadata_predicates: list[Any] = []

        for report_field in visible_fields:
            metadata_predicate = cls._metadata_row_predicate(
                base_form=base_form,
                report_field=report_field,
                tables=tables,
                join_paths=join_paths,
            )
            if metadata_predicate is not None:
                metadata_predicates.append(metadata_predicate)

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
        safe_sort_direction = "desc" if sort_direction == "desc" else "asc"
        order_expr = sort_expr.desc() if safe_sort_direction == "desc" else sort_expr.asc()

        result_query = select(*select_exprs).select_from(from_clause)
        all_predicates = [*metadata_predicates, *predicates]
        if all_predicates:
            result_query = result_query.where(and_(*all_predicates))
        if grouped_mode and group_by_exprs:
            result_query = result_query.group_by(*group_by_exprs)

        count_subquery = result_query.alias("report_count_subquery")
        count_query = select(func.count()).select_from(count_subquery)
        result_query = result_query.order_by(order_expr).limit(limit).offset(offset)

        engine = get_engine()
        with engine.begin() as connection:
            total = int(connection.execute(count_query).scalar_one())
            rows = [dict(row) for row in connection.execute(result_query).mappings().all()]

        return {
            "count": total,
            "columns": [
                {
                    "key": column.key,
                    "name": column.name,
                    "type": column.field_type,
                    "form_table": column.form_table,
                    "field_name": column.field_name,
                    "lookup_id": column.lookup_id,
                    "foreign_key_table": column.foreign_key_table,
                    "foreign_key_field": column.foreign_key_field,
                    "expression_type": column.expression_type,
                    "aggregation_type": column.aggregation_type,
                    "group_by_flag": column.group_by_flag,
                }
                for column in selected_columns
            ],
            "rows": rows,
        }

    @classmethod
    def _metadata_row_predicate(
        cls,
        *,
        base_form: Form,
        report_field: ReportField,
        tables: dict[str, Table],
        join_paths: dict[str, list[dict[str, str]]],
    ):
        if not (report_field.filter_expression or "").strip():
            return None
        if report_field.expression_type not in {ReportExpressionType.LATEST, ReportExpressionType.EXISTS}:
            return None

        related_form = report_field.related_form or report_field.form
        if not related_form and report_field.target_field:
            related_form = report_field.target_field.form
        if not related_form:
            return None

        related_table = tables[related_form.table_name]
        path = join_paths.get(related_form.table_name, [])
        sub_from, correlation_predicates = cls._build_correlated_from_clause(
            base_table_name=base_form.table_name,
            target_table_name=related_form.table_name,
            tables=tables,
            path=path,
        )

        filter_type = "Integer"
        if report_field.target_field:
            filter_type = report_field.target_field.type

        expr_filter = cls._report_field_filter_predicate(
            report_field=report_field,
            fallback_field_type=filter_type,
            related_table=related_table,
        )
        if expr_filter is None:
            return None

        combined = [*correlation_predicates, expr_filter]
        return exists(select(literal(1)).select_from(sub_from).where(and_(*combined)))

    @classmethod
    def _load_report(cls, *, report_id: int) -> Report:
        report = (
            Report.objects.select_related("base_form")
            .prefetch_related(
                "fields__form",
                "fields__form_field__form",
                "fields__target_field__form",
                "fields__related_form",
                "fields__sort_field__form",
            )
            .filter(id=report_id)
            .first()
        )
        if not report:
            raise ValidationException("Report does not exist", field="report_id")
        return report

    @classmethod
    def _assert_user_can_access_report(cls, *, user, report: Report) -> None:
        if not cls._can_list_table(user, report.base_form.table_name):
            raise PermissionDeniedException("User is not authorized for this operation")

    @classmethod
    def _build_report_columns(cls, *, base_form: Form, visible_fields: list[ReportField]) -> list[ReportColumn]:
        columns: list[ReportColumn] = []
        used_keys: set[str] = set()

        for report_field in sorted(visible_fields, key=lambda item: (item.display_order, item.id)):
            resolved = cls._resolve_target_ref(base_form=base_form, report_field=report_field)
            form_field = resolved.field
            form = resolved.form

            raw_name = report_field.display_name or form_field.name
            column_key = _normalize_key(raw_name)
            while column_key in used_keys:
                column_key = f"{column_key}_{report_field.id}"
            used_keys.add(column_key)

            columns.append(
                ReportColumn(
                    key=column_key,
                    name=raw_name,
                    form_table=form.table_name,
                    field_name=form_field.name,
                    field_type=form_field.type,
                    lookup_id=int(form_field.lookup_id) if form_field.lookup_id else None,
                    foreign_key_table=form_field.foreign_key_table or "",
                    foreign_key_field=form_field.foreign_key_field or "id",
                    expression_type=report_field.expression_type,
                    aggregation_type=report_field.aggregation_type,
                    group_by_flag=bool(report_field.group_by_flag),
                )
            )
        return columns

    @classmethod
    def _build_column_expression(
        cls,
        *,
        base_form: Form,
        report_field: ReportField,
        report_column: ReportColumn,
        tables: dict[str, Table],
        join_paths: dict[str, list[dict[str, str]]],
        grouped_mode: bool,
    ):
        expression_type = report_field.expression_type

        if expression_type == ReportExpressionType.DIRECT:
            return cls._direct_expression(report_column=report_column, tables=tables)

        if expression_type in {ReportExpressionType.AGGREGATE, ReportExpressionType.GROUPED_AGGREGATE}:
            if grouped_mode and expression_type == ReportExpressionType.GROUPED_AGGREGATE:
                return cls._grouped_aggregate_expression(
                    base_form=base_form,
                    report_field=report_field,
                    report_column=report_column,
                    tables=tables,
                )
            return cls._correlated_aggregate_expression(
                base_form=base_form,
                report_field=report_field,
                report_column=report_column,
                tables=tables,
                join_paths=join_paths,
            )

        if expression_type == ReportExpressionType.LATEST:
            return cls._latest_expression(
                base_form=base_form,
                report_field=report_field,
                report_column=report_column,
                tables=tables,
                join_paths=join_paths,
            )

        if expression_type == ReportExpressionType.EXISTS:
            return cls._exists_expression(
                base_form=base_form,
                report_field=report_field,
                report_column=report_column,
                tables=tables,
                join_paths=join_paths,
            )

        raise ValidationException("Unsupported report expression type", field="expression_type")

    @staticmethod
    def _direct_expression(*, report_column: ReportColumn, tables: dict[str, Table]):
        table = tables[report_column.form_table]
        if report_column.field_name not in table.c:
            raise ValidationException("Referenced form field does not exist physically", field=report_column.field_name)
        return table.c[report_column.field_name]

    @classmethod
    def _correlated_aggregate_expression(
        cls,
        *,
        base_form: Form,
        report_field: ReportField,
        report_column: ReportColumn,
        tables: dict[str, Table],
        join_paths: dict[str, list[dict[str, str]]],
    ):
        related_form = report_field.related_form or report_field.form
        if not related_form and report_field.target_field:
            related_form = report_field.target_field.form
        if not related_form:
            raise ValidationException("Aggregate expression requires related form", field=str(report_field.id))

        aggregate = report_field.aggregation_type
        related_table = tables[related_form.table_name]
        path = join_paths.get(related_form.table_name, [])

        sub_from, correlation_predicates = cls._build_correlated_from_clause(
            base_table_name=base_form.table_name,
            target_table_name=related_form.table_name,
            tables=tables,
            path=path,
        )

        if aggregate == ReportAggregationType.COUNT:
            metric_expr = func.count(literal(1))
            metric_type = "Integer"
        else:
            target_ref = cls._resolve_target_ref(base_form=base_form, report_field=report_field)
            if target_ref.form.table_name != related_form.table_name:
                raise ValidationException("Aggregate target field must belong to related form", field=str(report_field.id))
            target_column = related_table.c[target_ref.field.name]
            metric_expr = cls._aggregation_expression(aggregate=aggregate, expression=target_column)
            metric_type = target_ref.field.type

        subquery = select(metric_expr).select_from(sub_from)

        expr_filter = cls._report_field_filter_predicate(
            report_field=report_field,
            fallback_field_type=metric_type,
            related_table=related_table,
        )
        combined: list[Any] = []
        if expr_filter is not None:
            combined.append(expr_filter)
        combined.extend(correlation_predicates)
        if combined:
            subquery = subquery.where(and_(*combined))
        return subquery.scalar_subquery()

    @classmethod
    def _grouped_aggregate_expression(
        cls,
        *,
        base_form: Form,
        report_field: ReportField,
        report_column: ReportColumn,
        tables: dict[str, Table],
    ):
        related_form = report_field.related_form or report_field.form
        if not related_form and report_field.target_field:
            related_form = report_field.target_field.form
        if not related_form:
            raise ValidationException("Grouped aggregate requires related form", field=str(report_field.id))

        related_table = tables[related_form.table_name]
        aggregate = report_field.aggregation_type

        if aggregate == ReportAggregationType.COUNT:
            return func.count(literal(1))

        if report_column.field_name not in related_table.c:
            raise ValidationException("Referenced form field does not exist physically", field=report_column.field_name)

        return cls._aggregation_expression(aggregate=aggregate, expression=related_table.c[report_column.field_name])

    @classmethod
    def _latest_expression(
        cls,
        *,
        base_form: Form,
        report_field: ReportField,
        report_column: ReportColumn,
        tables: dict[str, Table],
        join_paths: dict[str, list[dict[str, str]]],
    ):
        target_ref = cls._resolve_target_ref(base_form=base_form, report_field=report_field)
        related_form = report_field.related_form or target_ref.form
        related_table = tables[related_form.table_name]

        if target_ref.field.name not in related_table.c:
            raise ValidationException("Referenced form field does not exist physically", field=target_ref.field.name)

        sort_field = report_field.sort_field or target_ref.field
        if sort_field.form_id != related_form.id:
            raise ValidationException("Latest sort field must belong to related form", field=str(report_field.id))
        if sort_field.name not in related_table.c:
            raise ValidationException("Latest sort field does not exist physically", field=sort_field.name)

        path = join_paths.get(related_form.table_name, [])
        sub_from, correlation_predicates = cls._build_correlated_from_clause(
            base_table_name=base_form.table_name,
            target_table_name=related_form.table_name,
            tables=tables,
            path=path,
        )

        target_expr = related_table.c[target_ref.field.name]
        subquery = select(target_expr).select_from(sub_from).where(target_expr.is_not(None))

        expr_filter = cls._report_field_filter_predicate(
            report_field=report_field,
            fallback_field_type=target_ref.field.type,
            related_table=related_table,
        )
        combined: list[Any] = []
        if expr_filter is not None:
            combined.append(expr_filter)
        combined.extend(correlation_predicates)
        if combined:
            subquery = subquery.where(and_(*combined))

        order_expr = related_table.c[sort_field.name].asc()
        if report_field.sort_direction == ReportSortDirection.DESC:
            order_expr = related_table.c[sort_field.name].desc()

        return subquery.order_by(order_expr).limit(1).scalar_subquery()

    @classmethod
    def _exists_expression(
        cls,
        *,
        base_form: Form,
        report_field: ReportField,
        report_column: ReportColumn,
        tables: dict[str, Table],
        join_paths: dict[str, list[dict[str, str]]],
    ):
        related_form = report_field.related_form or report_field.form
        if not related_form and report_field.target_field:
            related_form = report_field.target_field.form
        if not related_form:
            raise ValidationException("Exists expression requires related form", field=str(report_field.id))

        related_table = tables[related_form.table_name]
        path = join_paths.get(related_form.table_name, [])
        sub_from, correlation_predicates = cls._build_correlated_from_clause(
            base_table_name=base_form.table_name,
            target_table_name=related_form.table_name,
            tables=tables,
            path=path,
        )

        subquery = select(literal(1)).select_from(sub_from)

        filter_type = "Integer"
        if report_field.target_field:
            filter_type = report_field.target_field.type
            if report_field.target_field.form_id != related_form.id:
                raise ValidationException("Exists target field must belong to related form", field=str(report_field.id))

        expr_filter = cls._report_field_filter_predicate(
            report_field=report_field,
            fallback_field_type=filter_type,
            related_table=related_table,
        )
        combined: list[Any] = []
        if expr_filter is not None:
            combined.append(expr_filter)
        combined.extend(correlation_predicates)
        if combined:
            subquery = subquery.where(and_(*combined))

        return exists(subquery)

    @staticmethod
    def _aggregation_expression(*, aggregate: str, expression):
        if aggregate == ReportAggregationType.SUM:
            return func.sum(expression)
        if aggregate == ReportAggregationType.AVG:
            return func.avg(expression)
        if aggregate == ReportAggregationType.MIN:
            return func.min(expression)
        if aggregate == ReportAggregationType.MAX:
            return func.max(expression)
        if aggregate == ReportAggregationType.COUNT:
            return func.count(expression)
        raise ValidationException("Unsupported aggregation type", field="aggregation_type")

    @classmethod
    def _report_field_filter_predicate(
        cls,
        *,
        report_field: ReportField,
        fallback_field_type: str,
        related_table: Table,
    ):
        expression = cls._resolve_relative_filter_expression(
            (report_field.filter_expression or "").strip(),
            field_type=fallback_field_type,
        )
        if not expression:
            return None

        target_field = report_field.target_field
        if target_field:
            if target_field.name not in related_table.c:
                raise ValidationException("Filter target field does not exist physically", field=target_field.name)
            expression = cls._resolve_relative_filter_expression(expression, field_type=target_field.type)
            return FilterParser.parse(
                target_field.name,
                target_field.type,
                expression,
                related_table.c[target_field.name],
            )

        if "id" not in related_table.c:
            raise ValidationException("Related table does not contain id column", field=related_table.name)
        return FilterParser.parse("id", fallback_field_type, expression, related_table.c.id)

    @staticmethod
    def _resolve_relative_filter_expression(expression: str, *, field_type: str) -> str:
        if not expression or field_type not in {"Date", "DateTime"}:
            return expression

        def replacement(match: re.Match[str]) -> str:
            offset_raw = match.group(1)
            offset_days = int(offset_raw) if offset_raw else 0
            target_date = date.today() + timedelta(days=offset_days)
            if field_type == "DateTime":
                return datetime.combine(target_date, datetime.min.time()).isoformat(timespec="seconds")
            return target_date.isoformat()

        return re.sub(r"\bTODAY(?:([+-]\d+))?\b", replacement, expression)

    @classmethod
    def _build_correlated_from_clause(
        cls,
        *,
        base_table_name: str,
        target_table_name: str,
        tables: dict[str, Table],
        path: list[dict[str, str]],
    ) -> tuple[Any, list[Any]]:
        target_table = tables[target_table_name]
        if target_table_name == base_table_name:
            return target_table, []

        from_clause = target_table
        joined_tables = {target_table_name}
        correlation_predicates: list[Any] = []

        for edge in reversed(path):
            previous_table = cls._previous_table_in_path(edge=edge)
            join_condition = cls._edge_join_condition(edge=edge, tables=tables)

            if previous_table == base_table_name:
                correlation_predicates.append(join_condition)
                continue

            if previous_table not in joined_tables:
                from_clause = from_clause.join(tables[previous_table], join_condition)
                joined_tables.add(previous_table)

        if not correlation_predicates:
            raise ValidationException("Unable to correlate expression to base form", field=target_table_name)
        return from_clause, correlation_predicates

    @staticmethod
    def _previous_table_in_path(*, edge: dict[str, str]) -> str:
        if edge["next_table"] == edge["source_table"]:
            return edge["target_table"]
        return edge["source_table"]

    @classmethod
    def _resolve_target_ref(cls, *, base_form: Form, report_field: ReportField) -> ResolvedFieldRef:
        expression_type = report_field.expression_type

        if expression_type == ReportExpressionType.DIRECT:
            form_field = report_field.form_field or report_field.target_field
            form = report_field.form or (form_field.form if form_field else None) or base_form
            if not form_field:
                synthetic_field = FormField(
                    form=form,
                    name="id",
                    type="Integer",
                    mandatory=True,
                    unique=True,
                    foreign_key_table="",
                    foreign_key_field="id",
                )
                return ResolvedFieldRef(form=form, field=synthetic_field)
            if form_field.form_id != form.id:
                raise ValidationException("Direct field metadata is inconsistent", field=str(report_field.id))
            return ResolvedFieldRef(form=form, field=form_field)

        target_field = report_field.target_field or report_field.form_field
        if not target_field:
            if expression_type in {ReportExpressionType.EXISTS, ReportExpressionType.AGGREGATE, ReportExpressionType.GROUPED_AGGREGATE}:
                related_form = report_field.related_form or report_field.form
                if related_form is None:
                    related_form = base_form
                synthetic_field = FormField(
                    form=related_form,
                    name="id",
                    type="Integer",
                    mandatory=True,
                    unique=False,
                    foreign_key_table="",
                    foreign_key_field="id",
                )
                return ResolvedFieldRef(form=related_form, field=synthetic_field)
            raise ValidationException("Report expression is missing target_field", field=str(report_field.id))

        form = report_field.related_form or report_field.form or target_field.form
        if target_field.form_id != form.id:
            raise ValidationException("Report expression references mismatched target_field", field=str(report_field.id))
        return ResolvedFieldRef(form=form, field=target_field)

    @staticmethod
    def _forms_touched_by_field(*, base_form: Form, report_field: ReportField) -> list[Form]:
        forms: list[Form] = []
        for candidate in [
            report_field.form,
            report_field.related_form,
            report_field.form_field.form if report_field.form_field else None,
            report_field.target_field.form if report_field.target_field else None,
            report_field.sort_field.form if report_field.sort_field else None,
            base_form,
        ]:
            if candidate is None:
                continue
            if candidate.id in {form.id for form in forms}:
                continue
            forms.append(candidate)
        return forms

    @classmethod
    def _visible_report_fields(cls, *, user, report: Report) -> list[ReportField]:
        visible: list[ReportField] = []
        for report_field in report.fields.all():
            try:
                touched_forms = cls._forms_touched_by_field(base_form=report.base_form, report_field=report_field)
            except Exception:
                continue
            if not touched_forms:
                continue
            if not all(cls._can_list_table(user, form.table_name) for form in touched_forms):
                continue
            visible.append(report_field)
        return sorted(visible, key=lambda item: (item.display_order, item.id))

    @staticmethod
    def _can_list_table(user, table_name: str) -> bool:
        try:
            PermissionService.assert_table_permission(user, table_name, "list")
            return True
        except PermissionDeniedException:
            return False

    @classmethod
    def _apply_join_path(
        cls,
        *,
        from_clause,
        joined_tables: set[str],
        tables: dict[str, Table],
        path: list[dict[str, str]],
    ) -> tuple[Any, set[str]]:
        mutable_from = from_clause
        mutable_joined = set(joined_tables)

        for edge in path:
            next_table = edge["next_table"]
            if next_table in mutable_joined:
                continue
            join_condition = cls._edge_join_condition(edge=edge, tables=tables)
            mutable_from = mutable_from.join(tables[next_table], join_condition)
            mutable_joined.add(next_table)

        return mutable_from, mutable_joined

    @staticmethod
    def _edge_join_condition(*, edge: dict[str, str], tables: dict[str, Table]):
        return tables[edge["source_table"]].c[edge["source_column"]] == tables[edge["target_table"]].c[edge["target_column"]]

    @staticmethod
    @lru_cache(maxsize=64)
    def _reflect_tables_cached(table_names: tuple[str, ...]) -> dict[str, Table]:
        engine = get_engine()
        inspector = inspect(engine)
        metadata = MetaData()
        tables: dict[str, Table] = {}

        for table_name in table_names:
            if not inspector.has_table(table_name):
                raise ValidationException("Referenced form table does not exist", field=table_name)
            tables[table_name] = Table(table_name, metadata, autoload_with=engine)
        return tables

    @classmethod
    def _reflect_tables(cls, table_names: tuple[str, ...]) -> dict[str, Table]:
        return cls._reflect_tables_cached(tuple(sorted(set(table_names))))

    @staticmethod
    @lru_cache(maxsize=1)
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

    @classmethod
    def _find_join_path(
        cls,
        *,
        graph: dict[str, list[dict[str, str]]],
        base_table: str,
        target_table: str,
    ) -> list[dict[str, str]]:
        if base_table == target_table:
            return []

        cache_key = (base_table, target_table)
        if cache_key in cls._join_path_cache:
            return [dict(edge) for edge in cls._join_path_cache[cache_key]]

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
                    cls._join_path_cache[cache_key] = [dict(item) for item in next_path]
                    return next_path
                visited.add(next_table)
                queue.append((next_table, next_path))
        cls._join_path_cache[cache_key] = []
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


