from __future__ import annotations

import dash
import dash_mantine_components as dmc
from dash import dcc, html

from components.dynamic_table import build_empty_grid

dash.register_page(__name__, path_template="/menu/<menu_id>", name="Dynamic Page")


def layout(menu_id: str | None = None) -> html.Div:
    return html.Div(
        [
            dcc.Store(id="active-menu-id-hint", data=menu_id),
            dcc.Store(id="edit-row-store", data={}),
            dcc.Store(id="crud-action-local", data={"ts": 0, "action": ""}),
            dcc.Download(id="download-csv"),
            dmc.Group(
                [
                    dmc.Title(id="dynamic-page-title", order=2),
                    dmc.Badge(id="dynamic-page-table", color="indigo", variant="light"),
                ],
                justify="space-between",
                mb="md",
            ),
            html.Div(id="dynamic-filter-section"),
            html.Div(id="dynamic-toolbar"),
            html.Div(id="dynamic-grid-wrapper", children=build_empty_grid()),
            html.Div(id="dynamic-page-error", className="page-error"),
            dmc.Modal(
                id="insert-modal",
                opened=False,
                title="Insert Record",
                centered=True,
                size="xl",
                radius="lg",
                className="insert-modal",
                children=dmc.Stack(
                    [
                        dmc.Text("Fields marked with * are required. Locked fields are system-generated.", c="dimmed", size="sm", className="insert-modal-hint"),
                        dmc.Paper(id="insert-form-container", p="md", withBorder=True, radius="md", className="insert-form-card"),
                        dmc.Group(
                            [
                                dmc.Button("Cancel", id="insert-cancel", variant="default"),
                                dmc.Button("Insert", id="insert-confirm"),
                            ],
                            justify="flex-end",
                            className="insert-modal-actions",
                        ),
                        html.Div(id="insert-modal-error", className="page-error"),
                    ]
                ),
            ),
            dmc.Modal(
                id="edit-modal",
                opened=False,
                title="Edit Record",
                centered=True,
                size="xl",
                radius="lg",
                className="insert-modal",
                children=dmc.Stack(
                    [
                        dmc.Text("Edit fields and save changes.", c="dimmed", size="sm", className="insert-modal-hint"),
                        dmc.Paper(id="edit-form-container", p="md", withBorder=True, radius="md", className="insert-form-card"),
                        dmc.Group(
                            [
                                dmc.Button("Cancel", id="edit-cancel", variant="default"),
                                dmc.Button("Save", id="edit-confirm"),
                            ],
                            justify="flex-end",
                            className="insert-modal-actions",
                        ),
                        html.Div(id="edit-modal-error", className="page-error"),
                    ]
                ),
            ),
        ],
        className="dynamic-page",
    )


