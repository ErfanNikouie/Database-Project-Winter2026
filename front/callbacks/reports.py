from __future__ import annotations

import json
from io import StringIO

import pandas as pd
from dash import Input, Output, State, callback, dcc, no_update

from services.api_client import api_client
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
    State("report-filters-json", "value"),
    State("report-page-size", "value"),
    State("report-page", "value"),
    State("auth-store", "data"),
    prevent_initial_call=True,
)
def run_selected_report(
    run_clicks: int | None,
    report_id_value: str | None,
    sort_by_value: str | None,
    sort_direction_value: str | None,
    filters_json: str | None,
    page_size_raw: int | None,
    page_raw: int | None,
    auth_data: dict | None,
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
    filters_payload = _parse_filters_json(filters_json)
    if isinstance(filters_payload, str):
        return no_update, no_update, no_update, no_update, no_update, filters_payload
    sort_direction = sort_direction_value if sort_direction_value in {"asc", "desc"} else "asc"

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
    column_defs = [
        {
            "field": column["key"],
            "headerName": column["name"],
            "resizable": True,
            "sortable": True,
            "filter": True,
        }
        for column in columns
    ]
    result_store = {"columns": columns, "rows": rows, "count": count}
    count_text = f"Rows: {count}"
    return result_store, column_defs, rows, _grid_options(page_size), count_text, ""


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


def _parse_filters_json(raw_filters: str | None) -> dict | str:
    text = (raw_filters or "{}").strip()
    if not text:
        return {}
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return "Filters must be valid JSON"
    if not isinstance(parsed, dict):
        return "Filters JSON must be an object"
    return parsed


def _grid_options(page_size: int) -> dict:
    return {
        "rowSelection": "single",
        "pagination": True,
        "paginationPageSize": page_size,
        "animateRows": True,
    }


def _base_url() -> str:
    from api.base import DEFAULT_BASE_URL

    return DEFAULT_BASE_URL


