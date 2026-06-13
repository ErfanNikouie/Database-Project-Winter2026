from __future__ import annotations

from dash import dcc
from dash import html
import dash_ag_grid as dag
import dash_mantine_components as dmc


def build_dynamic_page_placeholders() -> html.Div:
    return html.Div(
        [
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
            # Mirror modal IDs so callbacks remain valid off the dynamic page route.
            dmc.Modal(id="insert-modal", opened=False, children=[]),
            dmc.Modal(id="edit-modal", opened=False, children=[]),
            dmc.Select(id="report-selector", data=[], value=None),
            dmc.TextInput(id="report-sort-by", value=""),
            dmc.Select(id="report-sort-direction", data=[{"value": "asc", "label": "asc"}], value="asc"),
            dmc.Textarea(id="report-filters-json", value="{}"),
            dmc.NumberInput(id="report-page-size", value=100),
            dmc.NumberInput(id="report-page", value=1),
            html.Div(id="report-error"),
            dcc.Store(id="report-result-store", data={"columns": [], "rows": [], "count": 0}),
            dcc.Download(id="report-download"),
            html.Div(id="report-count"),
            dag.AgGrid(
                id="report-grid",
                rowData=[],
                columnDefs=[],
                dashGridOptions={"pagination": True},
            ),
        ],
        style={"display": "none"},
    )

