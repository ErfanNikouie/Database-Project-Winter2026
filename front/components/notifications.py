from __future__ import annotations

import dash_mantine_components as dmc


def build_success(message: str) -> dmc.Alert:
    return dmc.Alert(title="Success", color="green", children=message)


def build_error(message: str) -> dmc.Alert:
    return dmc.Alert(title="Error", color="red", children=message)


def build_warning(message: str) -> dmc.Alert:
    return dmc.Alert(title="Warning", color="yellow", children=message)

