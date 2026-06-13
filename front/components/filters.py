from __future__ import annotations

from typing import Any

import dash_mantine_components as dmc
from dash import html

from utils.filter_help import FILTER_HELP_BY_TYPE
from utils.labels import humanize_field_name


def build_filter_section(
    *,
    fields: list[dict[str, Any]],
    fk_options_by_field: dict[str, list[dict[str, str]]] | None = None,
    lookup_options_by_field: dict[str, list[dict[str, str]]] | None = None,
) -> dmc.Accordion:
    controls = []
    fk_options = fk_options_by_field or {}
    lookup_options = lookup_options_by_field or {}
    for field in fields:
        name = field["name"]
        field_type = field["type"]
        field_id = {"type": "filter-field", "name": name}
        display_name = humanize_field_name(name)

        if field_type == "Boolean":
            control = dmc.Select(
                id=field_id,
                label=f"{display_name} ({field_type})",
                data=[
                    {"label": "Don't Care", "value": ""},
                    {"label": "True", "value": "True"},
                    {"label": "False", "value": "False"},
                ],
                value="",
            )
        elif field_type == "ForeignKey":
            control = dmc.Select(
                id=field_id,
                label=f"{display_name} ({field_type})",
                data=_sort_options_by_id(fk_options.get(name, [])),
                value=None,
                searchable=True,
                clearable=True,
            )
        elif field_type == "Lookup":
            control = dmc.Select(
                id=field_id,
                label=f"{display_name} ({field_type})",
                data=_sort_options_by_id(lookup_options.get(name, [])),
                value=None,
                searchable=True,
                clearable=True,
            )
        elif field_type == "Date":
            control = dmc.Stack(
                [
                    dmc.DateInput(
                        id={"type": "filter-date-bound", "name": name, "bound": "from"},
                        label=f"{display_name} From",
                        value=None,
                        clearable=True,
                    ),
                    dmc.DateInput(
                        id={"type": "filter-date-bound", "name": name, "bound": "to"},
                        label=f"{display_name} To",
                        value=None,
                        clearable=True,
                    ),
                ],
                gap="xs",
            )
        elif field_type == "DateTime":
            control = dmc.Stack(
                [
                    dmc.DateTimePicker(
                        id={"type": "filter-date-bound", "name": name, "bound": "from"},
                        label=f"{display_name} From",
                        value=None,
                        clearable=True,
                    ),
                    dmc.DateTimePicker(
                        id={"type": "filter-date-bound", "name": name, "bound": "to"},
                        label=f"{display_name} To",
                        value=None,
                        clearable=True,
                    ),
                ],
                gap="xs",
            )
        else:
            control = dmc.TextInput(
                id=field_id,
                label=f"{display_name} ({field_type})",
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


def _sort_options_by_id(options: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def key_fn(option: dict[str, Any]) -> tuple[int, int | str]:
        raw_value = option.get("value")
        try:
            return (0, int(float(str(raw_value))))
        except (TypeError, ValueError):
            return (1, str(raw_value or ""))

    return sorted(options, key=key_fn)


