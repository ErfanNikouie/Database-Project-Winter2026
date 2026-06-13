from __future__ import annotations

from typing import Any

import dash_ag_grid as dag
import dash_mantine_components as dmc

from utils.labels import humanize_field_name


def build_toolbar(
    *,
    can_insert: bool,
    can_delete: bool,
    can_print: bool,
    count: int,
    menu_index: int,
    page_size: int = 20,
    page_number: int = 1,
) -> dmc.Group:
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
            dmc.Select(
                id={"type": "toolbar-action", "action": "page-size", "index": menu_index},
                label="Page Size",
                data=[
                    {"value": "20", "label": "20"},
                    {"value": "50", "label": "50"},
                    {"value": "100", "label": "100"},
                ],
                value=str(page_size),
                w=100,
                allowDeselect=False,
            ),
            dmc.NumberInput(
                id={"type": "toolbar-action", "action": "page-number", "index": menu_index},
                label="Page",
                value=page_number,
                min=1,
                step=1,
                w=110,
                allowDecimal=False,
            ),
            dmc.Badge(f"Count: {count}", color="gray", variant="filled"),
        ],
        justify="space-between",
        align="center",
        mb="sm",
    )


def build_grid(*, rows: list[dict[str, Any]], columns: list[str], page_size: int = 20) -> dag.AgGrid:
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
            "paginationPageSize": page_size,
            "paginationPageSizeSelector": [20, 50, 100],
        },
        className="ag-theme-quartz-dark",
        style={"height": "62vh", "width": "100%"},
    )


def build_empty_grid(page_size: int = 20) -> Any:
    return dag.AgGrid(
        id="dynamic-grid",
        rowData=[],
        columnDefs=[],
        className="ag-theme-quartz-dark",
        dashGridOptions={
            "rowSelection": "single",
            "pagination": True,
            "paginationPageSize": page_size,
            "paginationPageSizeSelector": [20, 50, 100],
        },
        style={"height": "62vh", "width": "100%"},
    )

