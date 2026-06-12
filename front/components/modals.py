from __future__ import annotations

import dash_mantine_components as dmc


def build_record_modal(modal_id: str, title: str) -> dmc.Modal:
    return dmc.Modal(
        id=modal_id,
        title=title,
        opened=False,
        centered=True,
        size="lg",
        children=[],
    )


def build_delete_modal() -> dmc.Modal:
    return dmc.Modal(
        id="modal-delete-confirm",
        title="Confirm deletion",
        opened=False,
        centered=True,
        size="sm",
        children=dmc.Stack(
            [
                dmc.Text("Are you sure you want to delete this record?"),
                dmc.Group(
                    [
                        dmc.Button("Cancel", id="btn-delete-cancel", variant="default"),
                        dmc.Button("Delete", id="btn-delete-confirm", color="red"),
                    ],
                    justify="flex-end",
                ),
            ]
        ),
    )

