from __future__ import annotations

import dash
import dash_mantine_components as dmc
from dash import dcc, html

import dash_ag_grid as dag

dash.register_page(__name__, path="/reports/generate", name="Generate Report")


def layout() -> html.Div:
    return html.Div(
        [
            dcc.Store(id="report-result-store", data={"columns": [], "rows": [], "count": 0}),
            dcc.Download(id="report-download"),
            dmc.Group(
                [
                    dmc.Select(id="report-selector", label="Report", data=[], placeholder="Select report", searchable=True, w=320),
                    dmc.TextInput(id="report-sort-by", label="Sort By", value="", placeholder="Optional column key", w=220),
                    dmc.Select(
                        id="report-sort-direction",
                        label="Sort Direction",
                        data=[{"value": "asc", "label": "asc"}, {"value": "desc", "label": "desc"}],
                        value="asc",
                        w=150,
                        allowDeselect=False,
                    ),
                    dmc.NumberInput(id="report-page-size", label="Page Size", value=100, min=1, max=1000, w=130),
                    dmc.NumberInput(id="report-page", label="Page", value=1, min=1, step=1, w=110),
                    dmc.Button("Generate", id="report-run", mt=24),
                    dmc.Button("Export CSV", id="report-export", variant="outline", mt=24),
                ],
                align="end",
                mb="md",
                gap="sm",
            ),
            dmc.Textarea(
                id="report-filters-json",
                label="Filters (JSON)",
                description="Use report field keys. Example: {\"username\":\"John|Ali\"}",
                minRows=2,
                autosize=True,
                value="{}",
                mb="sm",
            ),
            dmc.Text(id="report-count", c="dimmed", mb="sm"),
            dag.AgGrid(
                id="report-grid",
                rowData=[],
                columnDefs=[],
                className="ag-theme-quartz-dark",
                dashGridOptions={
                    "rowSelection": "single",
                    "pagination": True,
                    "paginationPageSize": 100,
                    "animateRows": True,
                },
                style={"height": "62vh", "width": "100%"},
            ),
            html.Div(id="report-error", className="page-error"),
        ],
        className="dynamic-page",
    )


