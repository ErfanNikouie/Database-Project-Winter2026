from __future__ import annotations

import dash_mantine_components as dmc
from dash_iconify import DashIconify


def build_navbar() -> dmc.Group:
    return dmc.Group(
        [
            dmc.Group(
                [
                    DashIconify(icon="mdi:office-building", width=22),
                    dmc.Text("HRMS Dynamic Platform", fw=700, size="lg"),
                ],
                gap="sm",
            ),
            dmc.Group(
                [
                    dmc.Button("Profile", id="btn-profile", variant="subtle"),
                    dmc.Button("Logout", id="btn-logout", color="red", variant="light"),
                ],
                gap="sm",
            ),
        ],
        justify="space-between",
        align="center",
        className="top-navbar",
    )

