from __future__ import annotations

import dash
import dash_mantine_components as dmc
from dash import html

dash.register_page(__name__, path="/login", name="Login")


def layout() -> html.Div:
    return html.Div(
        dmc.Center(
            dmc.Paper(
                [
                    dmc.Title("Welcome back", order=2),
                    dmc.Text("Sign in to HRMS Dynamic Enterprise Platform", c="dimmed", mb="md"),
                    dmc.TextInput(id="login-username", label="Username"),
                    dmc.PasswordInput(id="login-password", label="Password", mt="sm"),
                    dmc.Checkbox(id="login-remember", label="Remember me", checked=True, mt="md"),
                    dmc.Button("Login", id="login-submit", fullWidth=True, mt="lg"),
                    html.Div(id="login-error", className="page-error"),
                ],
                radius="md",
                p="xl",
                withBorder=True,
                className="login-card",
            ),
            h="80vh",
        ),
        className="login-page",
    )

