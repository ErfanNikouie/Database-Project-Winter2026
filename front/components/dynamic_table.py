from __future__ import annotations

from typing import Any

import dash_ag_grid as dag
import dash_mantine_components as dmc

from utils.labels import humanize_field_name


def build_toolbar(*, can_insert: bool, can_delete: bool, can_print: bool, count: int, menu_index: int) -> dmc.Group:
    return dmc.Group(
        [
            dmc.Button(
                "Insert",
                id={"type": "toolbar-action", "action": "insert", "index": menu_index},
                disabled=not can_insert,
            ),
            dmc.Button(
                "Refresh",
                id={"type": "toolbar-action", "action": "refresh", "index": menu_index},
                variant="default",
            ),
            dmc.Button(
                "Delete",
                id={"type": "toolbar-action", "action": "delete", "index": menu_index},
                disabled=not can_delete,
                color="red",
                variant="light",
            ),
            dmc.Button(
                "Export CSV",
                id={"type": "toolbar-action", "action": "export", "index": menu_index},
                disabled=not can_print,
                variant="outline",
            ),
            dmc.Badge(f"Count: {count}", color="gray", variant="filled"),
        ],
        justify="space-between",
        align="center",
        mb="sm",
    )


def build_grid(*, rows: list[dict[str, Any]], columns: list[str]) -> dag.AgGrid:
    column_defs = [
        {
            "field": col,
            "headerName": humanize_field_name(col),
            "resizable": True,
            "sortable": True,
            "filter": True,
        }
        for col in columns
    ]
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
        className="ag-theme-quartz-dark",
        style={"height": "62vh", "width": "100%"},
    )


def build_empty_grid() -> Any:
    return dag.AgGrid(
        id="dynamic-grid",
        rowData=[],
        columnDefs=[],
        className="ag-theme-quartz-dark",
        dashGridOptions={"rowSelection": "single", "pagination": True, "paginationPageSize": 50},
        style={"height": "62vh", "width": "100%"},
    )

