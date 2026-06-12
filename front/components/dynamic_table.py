from __future__ import annotations

from typing import Any

import dash_ag_grid as dag
import dash_mantine_components as dmc
from dash import html


def build_toolbar(*, can_insert: bool, can_delete: bool, can_print: bool, count: int) -> dmc.Group:
    return dmc.Group(
        [
            dmc.Button("Insert", id="btn-insert", disabled=not can_insert),
            dmc.Button("Refresh", id="btn-refresh", variant="default"),
            dmc.Button("Delete", id="btn-delete", disabled=not can_delete, color="red", variant="light"),
            dmc.Button("Export CSV", id="btn-export", disabled=not can_print, variant="outline"),
            dmc.Badge(f"Count: {count}", color="gray", variant="filled"),
        ],
        justify="space-between",
        align="center",
        mb="sm",
    )


def build_grid(*, rows: list[dict[str, Any]], columns: list[str]) -> dag.AgGrid:
    column_defs = [{"field": col, "resizable": True, "sortable": True, "filter": True} for col in columns]
    return dag.AgGrid(
        id="dynamic-grid",
        rowData=rows,
        columnDefs=column_defs,
        defaultColDef={"editable": False},
        dashGridOptions={
            "rowSelection": "single",
            "animateRows": True,
            "pagination": True,
            "paginationPageSize": 50,
        },
        className="ag-theme-alpine-dark",
        style={"height": "62vh", "width": "100%"},
    )


def build_empty_grid() -> html.Div:
    return html.Div("No records to display", className="empty-grid")

