from __future__ import annotations

from io import StringIO
from typing import Any

import dash_mantine_components as dmc
import pandas as pd
from dash import ALL, Input, Output, State, callback, dcc, html, no_update

from services.api_client import api_client
from services.display_service import enrich_rows_for_display
from utils.filter_help import FILTER_HELP_BY_TYPE
from utils.models import ApiError


@callback(
    Output("report-selector", "data"),
    Output("report-selector", "value"),
    Output("report-error", "children"),
    Input("_pages_location", "pathname"),
    Input("auth-store", "data"),
    State("report-selector", "value"),
    prevent_initial_call=False,
)
def load_available_reports(pathname: str | None, auth_data: dict | None, selected_report: str | None):
    if pathname != "/reports/generate":
        return no_update, no_update, no_update
    if not auth_data or not auth_data.get("authenticated"):
        return [], None, ""

    try:
        reports = api_client.get_available_reports(
            base_url=_base_url(),
            access_token=auth_data["access_token"],
        )
    except ApiError as exc:
        return [], None, exc.message

    options = [{"value": str(item["id"]), "label": item["name"]} for item in reports]
    available_ids = {option["value"] for option in options}
    next_selected = selected_report if selected_report in available_ids else (options[0]["value"] if options else None)
    return options, next_selected, ""


@callback(
    Output("report-definition-store", "data"),
    Output("report-filter-section", "children"),
    Output("report-sort-by", "data"),
    Output("report-sort-by", "value"),
    Output("report-error", "children", allow_duplicate=True),
    Input("report-selector", "value"),
    State("_pages_location", "pathname"),
    State("auth-store", "data"),
    prevent_initial_call=True,
)
def load_report_definition(report_id_value: str | None, pathname: str | None, auth_data: dict | None):
    if pathname != "/reports/generate":
        return no_update, no_update, no_update, no_update, no_update
    if not report_id_value:
        return {"fields": []}, html.Div(), [], None, ""
    if not auth_data or not auth_data.get("authenticated"):
        return {"fields": []}, html.Div(), [], None, "Authentication required"

    try:
        definition = api_client.get_report_definition(
            base_url=_base_url(),
            access_token=auth_data["access_token"],
            report_id=int(report_id_value),
        )
    except ApiError as exc:
        return {"fields": []}, html.Div(), [], None, exc.message

    fields = definition.get("fields") or []
    fk_options = _build_fk_filter_options(fields=fields, access_token=auth_data["access_token"])
    lookup_options = _build_lookup_filter_options(fields=fields, access_token=auth_data["access_token"])
    sort_options = [{"value": field["key"], "label": field["name"]} for field in fields]
    default_sort = sort_options[0]["value"] if sort_options else None
    return (
        definition,
        _build_filter_controls(fields, fk_options, lookup_options),
        sort_options,
        default_sort,
        "",
    )


@callback(
    Output("report-result-store", "data"),
    Output("report-grid", "columnDefs"),
    Output("report-grid", "rowData"),
    Output("report-grid", "dashGridOptions"),
    Output("report-count", "children"),
    Output("report-error", "children", allow_duplicate=True),
    Input("report-run", "n_clicks"),
    State("report-selector", "value"),
    State("report-sort-by", "value"),
    State("report-sort-direction", "value"),
    State("report-page-size", "value"),
    State("report-page", "value"),
    State("auth-store", "data"),
    State("report-definition-store", "data"),
    State({"type": "report-filter-field", "key": ALL}, "id"),
    State({"type": "report-filter-field", "key": ALL}, "value"),
    State({"type": "report-filter-date-bound", "key": ALL, "bound": ALL}, "id"),
    State({"type": "report-filter-date-bound", "key": ALL, "bound": ALL}, "value"),
    prevent_initial_call=True,
)
def run_selected_report(
    run_clicks: int | None,
    report_id_value: str | None,
    sort_by_value: str | None,
    sort_direction_value: str | None,
    page_size_raw: int | None,
    page_raw: int | None,
    auth_data: dict | None,
    report_definition: dict | None,
    filter_ids: list[dict[str, Any]] | None,
    filter_values: list[Any] | None,
    date_filter_ids: list[dict[str, Any]] | None,
    date_filter_values: list[Any] | None,
):
    if not run_clicks:
        return no_update, no_update, no_update, no_update, no_update, no_update
    if not auth_data or not auth_data.get("authenticated"):
        return no_update, no_update, no_update, no_update, no_update, "Authentication required"
    if not report_id_value:
        return no_update, no_update, no_update, no_update, no_update, "Select a report"

    page_size = _safe_int(page_size_raw, fallback=100, min_value=1, max_value=1000)
    page = _safe_int(page_raw, fallback=1, min_value=1, max_value=1000000)
    offset = (page - 1) * page_size
    sort_direction = sort_direction_value if sort_direction_value in {"asc", "desc"} else "asc"

    filters_payload = _build_filters(filter_ids, filter_values, date_filter_ids, date_filter_values)

    try:
        report_data = api_client.run_report(
            base_url=_base_url(),
            access_token=auth_data["access_token"],
            payload={
                "report_id": int(report_id_value),
                "filters": filters_payload,
                "sort_by": sort_by_value or "",
                "sort_direction": sort_direction,
                "limit": page_size,
                "offset": offset,
            },
        )
    except ApiError as exc:
        return {"columns": [], "rows": [], "count": 0}, [], [], _grid_options(page_size), "", exc.message

    columns = report_data.get("columns", [])
    rows = report_data.get("rows", [])
    count = int(report_data.get("count", 0))
    schema = {
        "fields": [
            {
                "name": column.get("key"),
                "type": column.get("type"),
                "lookup_id": column.get("lookup_id"),
                "foreign_key_table": column.get("foreign_key_table"),
                "foreign_key_field": column.get("foreign_key_field"),
            }
            for column in columns
        ]
    }
    display_rows, display_columns = enrich_rows_for_display(
        base_url=_base_url(),
        access_token=auth_data["access_token"],
        schema=schema,
        rows=rows,
    )
    column_defs = [
        {
            "field": col_name,
            "headerName": _column_header(col_name, columns),
            "resizable": True,
            "sortable": True,
            "filter": True,
        }
        for col_name in display_columns
    ]
    result_store = {"columns": columns, "rows": display_rows, "count": count}
    count_text = f"Rows: {count}"
    return result_store, column_defs, display_rows, _grid_options(page_size), count_text, ""


@callback(
    Output("report-download", "data"),
    Input("report-export", "n_clicks"),
    State("report-result-store", "data"),
    prevent_initial_call=True,
)
def export_report_csv(n_clicks: int | None, report_result: dict):
    if not n_clicks:
        return no_update
    rows = (report_result or {}).get("rows") or []
    columns = (report_result or {}).get("columns") or []
    if not rows or not columns:
        return no_update

    ordered_keys = [column["key"] for column in columns]
    ordered_names = [column["name"] for column in columns]
    df = pd.DataFrame(rows)
    for key in ordered_keys:
        if key not in df.columns:
            df[key] = None
    df = df[ordered_keys]
    df.columns = ordered_names

    buffer = StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    return dcc.send_string(buffer.getvalue(), "report.csv")


def _build_filter_controls(
    fields: list[dict[str, Any]],
    fk_options_by_key: dict[str, list[dict[str, str]]],
    lookup_options_by_key: dict[str, list[dict[str, str]]],
) -> html.Div:
    controls: list[Any] = []
    for field in fields:
        key = field.get("key")
        field_type = field.get("type")
        label = field.get("name") or key
        if not key:
            continue

        if field_type == "Boolean":
            controls.append(
                dmc.Select(
                    id={"type": "report-filter-field", "key": key},
                    label=f"{label} ({field_type})",
                    data=[
                        {"label": "Don't Care", "value": ""},
                        {"label": "True", "value": "True"},
                        {"label": "False", "value": "False"},
                    ],
                    value="",
                )
            )
            continue

        if field_type == "ForeignKey":
            controls.append(
                dmc.Select(
                    id={"type": "report-filter-field", "key": key},
                    label=f"{label} ({field_type})",
                    data=fk_options_by_key.get(key, []),
                    value=None,
                    searchable=True,
                    clearable=True,
                )
            )
            continue

        if field_type == "Lookup":
            controls.append(
                dmc.Select(
                    id={"type": "report-filter-field", "key": key},
                    label=f"{label} ({field_type})",
                    data=lookup_options_by_key.get(key, []),
                    value=None,
                    searchable=True,
                    clearable=True,
                )
            )
            continue

        if field_type == "Date":
            controls.append(
                dmc.Stack(
                    [
                        dmc.DateInput(
                            id={"type": "report-filter-date-bound", "key": key, "bound": "from"},
                            label=f"{label} From",
                            value=None,
                            clearable=True,
                        ),
                        dmc.DateInput(
                            id={"type": "report-filter-date-bound", "key": key, "bound": "to"},
                            label=f"{label} To",
                            value=None,
                            clearable=True,
                        ),
                    ],
                    gap="xs",
                )
            )
            continue

        if field_type == "DateTime":
            controls.append(
                dmc.Stack(
                    [
                        dmc.DateTimePicker(
                            id={"type": "report-filter-date-bound", "key": key, "bound": "from"},
                            label=f"{label} From",
                            value=None,
                            clearable=True,
                        ),
                        dmc.DateTimePicker(
                            id={"type": "report-filter-date-bound", "key": key, "bound": "to"},
                            label=f"{label} To",
                            value=None,
                            clearable=True,
                        ),
                    ],
                    gap="xs",
                )
            )
            continue

        controls.append(
            dmc.TextInput(
                id={"type": "report-filter-field", "key": key},
                label=f"{label} ({field_type})",
                placeholder=FILTER_HELP_BY_TYPE.get(field_type, ""),
            )
        )

    return dmc.Accordion(
        [
            dmc.AccordionItem(
                [
                    dmc.AccordionControl("Filters"),
                    dmc.AccordionPanel(html.Div(controls, className="filter-grid")),
                ],
                value="report-filters",
            )
        ],
        value=[],
    )


def _build_filters(
    filter_ids: list[dict[str, Any]] | None,
    filter_values: list[Any] | None,
    date_filter_ids: list[dict[str, Any]] | None,
    date_filter_values: list[Any] | None,
) -> dict[str, Any]:
    filters: dict[str, Any] = {}
    for field_id, value in zip(filter_ids or [], filter_values or []):
        if not isinstance(field_id, dict):
            continue
        key = field_id.get("key")
        if not key or value in (None, ""):
            continue
        filters[str(key)] = value

    date_bounds: dict[str, dict[str, Any]] = {}
    for field_id, value in zip(date_filter_ids or [], date_filter_values or []):
        if not isinstance(field_id, dict):
            continue
        key = field_id.get("key")
        bound = field_id.get("bound")
        if not key or bound not in {"from", "to"} or value in (None, ""):
            continue
        date_bounds.setdefault(str(key), {})[str(bound)] = value

    for key, bounds in date_bounds.items():
        clauses: list[str] = []
        if "from" in bounds:
            clauses.append(f">={_to_filter_literal(bounds['from'])}")
        if "to" in bounds:
            clauses.append(f"<={_to_filter_literal(bounds['to'])}")
        if clauses:
            filters[key] = "&".join(clauses)

    return filters


def _to_filter_literal(value: Any) -> str:
    text = str(value)
    if " " in text and "T" not in text:
        return text.replace(" ", "T")
    return text


def _safe_int(raw: int | None, *, fallback: int, min_value: int, max_value: int) -> int:
    try:
        value = int(raw if raw is not None else fallback)
    except (TypeError, ValueError):
        value = fallback
    if value < min_value:
        return min_value
    if value > max_value:
        return max_value
    return value


def _grid_options(page_size: int) -> dict:
    return {
        "rowSelection": "single",
        "pagination": True,
        "paginationPageSize": page_size,
        "animateRows": True,
    }


def _build_fk_filter_options(*, fields: list[dict[str, Any]], access_token: str) -> dict[str, list[dict[str, str]]]:
    options: dict[str, list[dict[str, str]]] = {}
    for field in fields:
        key = field.get("key")
        foreign_key_table = field.get("foreign_key_table")
        if not key or field.get("type") != "ForeignKey" or not foreign_key_table:
            continue
        try:
            rows = api_client.list_options(
                base_url=_base_url(),
                access_token=access_token,
                payload={"table": foreign_key_table, "limit": 200, "query": ""},
            )
        except ApiError:
            options[str(key)] = []
            continue
        rows = sorted(rows, key=lambda row: int(row["id"]))
        options[str(key)] = [
            {"value": str(row["id"]), "label": f"{row['id']}. {row['label']}"}
            for row in rows
        ]
    return options


def _build_lookup_filter_options(*, fields: list[dict[str, Any]], access_token: str) -> dict[str, list[dict[str, str]]]:
    options: dict[str, list[dict[str, str]]] = {}
    for field in fields:
        key = field.get("key")
        lookup_id = field.get("lookup_id")
        if not key or field.get("type") != "Lookup" or not lookup_id:
            continue
        try:
            rows = api_client.list_rows(
                base_url=_base_url(),
                access_token=access_token,
                payload={
                    "form": "LookupValue",
                    "limit": 1000,
                    "offset": 0,
                    "sort_by": "value",
                    "sort_direction": "asc",
                    "filters": {"lookup_id": int(lookup_id)},
                },
            ).get("items", [])
        except ApiError:
            options[str(key)] = []
            continue
        options[str(key)] = [
            {"value": str(row["id"]), "label": f"{row['id']}. {row.get('value', row['id'])}"}
            for row in rows
        ]
    return options


def _column_header(column_key: str, columns_meta: list[dict[str, Any]]) -> str:
    if column_key.endswith("__label"):
        base_key = column_key[: -len("__label")]
        for column in columns_meta:
            if column.get("key") == base_key:
                return f"{column.get('name', base_key)} Label"
        return column_key
    for column in columns_meta:
        if column.get("key") == column_key:
            return str(column.get("name") or column_key)
    return column_key


def _base_url() -> str:
    from api.base import DEFAULT_BASE_URL

    return DEFAULT_BASE_URL
