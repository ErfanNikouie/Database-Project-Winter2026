from __future__ import annotations

from typing import Any

import dash_mantine_components as dmc
from dash import html

from utils.filter_help import FILTER_HELP_BY_TYPE


def build_filter_section(*, fields: list[dict[str, Any]]) -> dmc.Accordion:
    controls = []
    for field in fields:
        name = field["name"]
        field_type = field["type"]
        field_id = {"type": "filter-field", "name": name}

        if field_type == "Boolean":
            control = dmc.Select(
                id=field_id,
                label=f"{name} ({field_type})",
                data=[
                    {"label": "Don't Care", "value": ""},
                    {"label": "True", "value": "True"},
                    {"label": "False", "value": "False"},
                ],
                value="",
            )
        else:
            control = dmc.TextInput(
                id=field_id,
                label=f"{name} ({field_type})",
                placeholder=FILTER_HELP_BY_TYPE.get(field_type, ""),
            )
        controls.append(control)

    return dmc.Accordion(
        [
            dmc.AccordionItem(
                [
                    dmc.AccordionControl("Filters"),
                    dmc.AccordionPanel(html.Div(controls, className="filter-grid")),
                ],
                value="filters",
            )
        ],
        value=[],
    )

