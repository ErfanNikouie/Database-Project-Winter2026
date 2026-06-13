from __future__ import annotations

from typing import Any

from services.api_client import api_client
from utils.models import ApiError


def enrich_rows_for_display(
    *,
    base_url: str,
    access_token: str,
    schema: dict[str, Any],
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    fields = schema.get("fields", [])
    label_columns_by_field: dict[str, str] = {}
    ordered_field_names = _ordered_schema_fields(fields)

    if not rows:
        columns: list[str] = []
        for name in ordered_field_names:
            columns.append(name)
            field = _field_by_name(fields, name)
            if field.get("type") in {"ForeignKey", "Lookup"}:
                columns.append(f"{name}__label")
        return rows, columns

    display_rows = [dict(row) for row in rows]

    for field in fields:
        name = field.get("name")
        if not name:
            continue

        field_type = field.get("type")
        if field_type == "ForeignKey" and field.get("foreign_key_table"):
            ids = sorted({int(row[name]) for row in rows if isinstance(row.get(name), int)})
            if not ids:
                continue
            label_map = _load_foreign_key_label_map(
                base_url=base_url,
                access_token=access_token,
                foreign_key_table=str(field["foreign_key_table"]),
                ids=ids,
            )
            label_column = f"{name}__label"
            label_columns_by_field[name] = label_column
            for row in display_rows:
                value = row.get(name)
                if isinstance(value, int):
                    label = label_map.get(value, "")
                    row[label_column] = label or ""
                else:
                    row[label_column] = ""

        if field_type == "Lookup" and field.get("lookup_id"):
            lookup_id = int(field["lookup_id"])
            try:
                lookup_values = api_client.list_rows(
                    base_url=base_url,
                    access_token=access_token,
                    payload={
                        "form": "LookupValue",
                        "limit": 1000,
                        "offset": 0,
                        "sort_by": "value",
                        "sort_direction": "asc",
                        "filters": {"lookup_id": lookup_id},
                    },
                ).get("items", [])
            except ApiError:
                lookup_values = []
            lookup_map = {int(item["id"]): str(item["value"]) for item in lookup_values if isinstance(item.get("id"), int)}
            lookup_value_to_id = {value: key for key, value in lookup_map.items()}
            label_column = f"{name}__label"
            label_columns_by_field[name] = label_column
            for row in display_rows:
                value = row.get(name)
                if isinstance(value, int):
                    row[label_column] = lookup_map.get(value, "")
                elif isinstance(value, str):
                    text_value = value.strip()
                    resolved_id = lookup_value_to_id.get(text_value)
                    if resolved_id is not None:
                        row[name] = resolved_id
                        row[label_column] = lookup_map.get(resolved_id, text_value)
                    else:
                        row[label_column] = text_value
                else:
                    row[label_column] = ""

    base_columns: list[str] = []
    for name in ordered_field_names:
        base_columns.append(name)
        label_column = label_columns_by_field.get(name)
        if label_column:
            base_columns.append(label_column)

    # Keep any server-provided columns that are not in schema ordering.
    extra_columns = [col for col in display_rows[0].keys() if col not in base_columns]
    id_like_extras = [col for col in extra_columns if col in {"id", "base_id"}]
    non_id_extras = [col for col in extra_columns if col not in {"id", "base_id"}]
    base_columns = [*id_like_extras, *base_columns, *non_id_extras]

    return display_rows, base_columns


def _ordered_schema_fields(fields: list[dict[str, Any]]) -> list[str]:
    scalar_fields: list[str] = []
    relational_fields: list[str] = []
    id_fields: list[str] = []

    for field in fields:
        name = field.get("name")
        if not name:
            continue
        name = str(name)
        if name in {"id", "base_id"}:
            id_fields.append(name)
            continue

        if field.get("type") in {"ForeignKey", "Lookup"}:
            relational_fields.append(name)
        else:
            scalar_fields.append(name)

    ordered: list[str] = []
    # Keep id-like columns visible first for consistency with form/crud pages.
    ordered.extend(id_fields)
    ordered.extend(scalar_fields)
    ordered.extend(relational_fields)
    return ordered


def _field_by_name(fields: list[dict[str, Any]], name: str) -> dict[str, Any]:
    for field in fields:
        if field.get("name") == name:
            return field
    return {}


def _load_foreign_key_label_map(
    *,
    base_url: str,
    access_token: str,
    foreign_key_table: str,
    ids: list[int],
) -> dict[int, str]:
    label_map: dict[int, str] = {}
    try:
        options = api_client.list_options(
            base_url=base_url,
            access_token=access_token,
            payload={
                "table": foreign_key_table,
                "ids": ids,
                "limit": max(50, len(ids)),
            },
        )
        label_map = {int(opt["id"]): str(opt["label"]) for opt in options}
    except ApiError:
        return {}

    if foreign_key_table != "employee":
        return label_map

    # Employee FKs should display full name for readability.
    employee_name_map = _load_employee_full_name_map(base_url=base_url, access_token=access_token, ids=ids)
    if employee_name_map:
        label_map.update(employee_name_map)
    return label_map


def _load_employee_full_name_map(*, base_url: str, access_token: str, ids: list[int]) -> dict[int, str]:
    try:
        listing = api_client.list_rows(
            base_url=base_url,
            access_token=access_token,
            payload={
                "form": "Employee",
                "limit": max(50, len(ids)),
                "offset": 0,
                "sort_by": "id",
                "sort_direction": "asc",
                "filters": {"id": "|".join(str(value) for value in ids)},
            },
        )
    except ApiError:
        return {}

    full_name_map: dict[int, str] = {}
    for item in listing.get("items", []):
        employee_id = item.get("id")
        if not isinstance(employee_id, int):
            continue
        first_name = str(item.get("first_name") or "").strip()
        last_name = str(item.get("last_name") or "").strip()
        full_name = " ".join(part for part in [first_name, last_name] if part).strip()
        if full_name:
            full_name_map[employee_id] = full_name
    return full_name_map


