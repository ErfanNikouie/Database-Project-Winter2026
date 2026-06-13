from __future__ import annotations

from dash import dcc
from dash import html
import dash_ag_grid as dag
import dash_mantine_components as dmc


def build_dynamic_page_placeholders() -> html.Div:
    return build_callback_placeholders()


def build_callback_placeholders(*, include_report_ids: bool = True) -> html.Div:
    children = [
        html.Div(id="dynamic-page-title"),
        html.Div(id="dynamic-page-table"),
        html.Div(id="dynamic-filter-section"),
        html.Div(id="insert-form-container"),
        html.Div(id="edit-form-container"),
        html.Div(id="dynamic-toolbar"),
        html.Div(id="dynamic-grid-wrapper"),
        html.Div(id="dynamic-page-error"),
        html.Div(id="insert-modal-error"),
        html.Div(id="edit-modal-error"),
        dcc.Store(id="edit-row-store", data={}),
        dcc.Store(id="crud-action-local", data={"ts": 0, "action": ""}),
        dcc.Download(id="download-csv"),
        dmc.Modal(id="insert-modal", opened=False, children=[]),
        dmc.Modal(id="edit-modal", opened=False, children=[]),
        dag.AgGrid(
            id="dynamic-grid",
            rowData=[],
            columnDefs=[],
            dashGridOptions={"pagination": True},
        ),
    ]

    if include_report_ids:
        children.extend(
            [
                dmc.Select(id="report-selector", data=[], value=None),
                dmc.Select(id="report-sort-by", data=[], value=None),
                dmc.Select(id="report-sort-direction", data=[{"value": "asc", "label": "asc"}], value="asc"),
                dcc.Store(id="report-definition-store", data={"fields": []}),
                dmc.NumberInput(id="report-page-size", value=100),
                dmc.NumberInput(id="report-page", value=1),
                html.Div(id="report-error"),
                dcc.Store(id="report-result-store", data={"columns": [], "rows": [], "count": 0}),
                dcc.Download(id="report-download"),
                html.Div(id="report-count"),
                html.Div(id="report-filter-section"),
                dag.AgGrid(
                    id="report-grid",
                    rowData=[],
                    columnDefs=[],
                    dashGridOptions={"pagination": True},
                ),
            ]
        )

    return html.Div(
        children,
        style={"display": "none"},
    )

