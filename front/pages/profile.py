from __future__ import annotations

import dash
import dash_mantine_components as dmc
from dash import html

dash.register_page(__name__, path="/profile", name="Profile")


def layout() -> html.Div:
    return html.Div(
        dmc.Container(
            [
                dmc.Title("My Profile", order=2, mb="md"),
                dmc.Paper(
                    [
                        dmc.TextInput(id="profile-username", label="Username"),
                        dmc.TextInput(id="profile-active", label="Active", disabled=True, mt="sm"),
                        dmc.TextInput(id="profile-groups", label="Groups", disabled=True, mt="sm"),
                        dmc.Divider(my="md"),
                        dmc.PasswordInput(id="profile-current-password", label="Current password"),
                        dmc.PasswordInput(id="profile-new-password", label="New password", mt="sm"),
                        dmc.PasswordInput(id="profile-confirm-password", label="Confirm new password", mt="sm"),
                        dmc.Button("Save profile", id="profile-save", mt="lg"),
                        html.Div(id="profile-error", className="page-error"),
                    ],
                    p="lg",
                    radius="md",
                    withBorder=True,
                ),
            ],
            fluid=True,
        )
    )

