from __future__ import annotations

from datetime import date
from typing import Any

import streamlit as st

from db.models import FormField
from services.crud_service import CrudService
from services.lookup_service import LookupService


def _parse_iso_date(value: Any) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except Exception:
        return None


def render_dynamic_inputs(
    fields: list[FormField],
    *,
    values: dict[str, Any] | None = None,
    key_prefix: str = "dyn",
) -> tuple[dict[str, Any], list[str]]:
    """Render Streamlit widgets for form fields.

    Returns: (data, validation_errors)
    """

    values = values or {}
    data: dict[str, Any] = {}
    errors: list[str] = []

    lookup_service = LookupService()
    crud_service = CrudService()

    def row_label(row: dict[str, Any]) -> str:
        """Best-effort label for FK dropdown items."""
        for key in ("Name", "Description", "Title"):
            v = row.get(key)
            if v is not None and str(v).strip():
                return str(v)
        if row.get("FirstName") or row.get("LastName"):
            return (f"{row.get('FirstName') or ''} {row.get('LastName') or ''}").strip() or f"#{row.get('Id')}"
        # fall back to the first non-Id column
        for k, v in row.items():
            if k == "Id":
                continue
            if v is not None and str(v).strip():
                return f"{k}={v}"
        return f"#{row.get('Id')}"

    for f in fields:
        label = f.FieldName + (" *" if f.Mandatory else "")
        widget_key = f"{key_prefix}_{f.Id}"

        if f.FieldType == "text":
            v = st.text_input(label, value=str(values.get(f.FieldName) or ""), key=widget_key)
            if f.Mandatory and not v.strip():
                errors.append(f"{f.FieldName} is mandatory")
            data[f.FieldName] = v.strip() if v.strip() else None

        elif f.FieldType in {"number", "integer"}:
            raw = values.get(f.FieldName)
            if raw is None or raw == "":
                raw = 0
            try:
                raw_num = float(raw)
            except Exception:
                raw_num = 0

            if f.FieldType == "integer":
                v = st.number_input(label, value=int(raw_num), step=1, key=widget_key)
                data[f.FieldName] = int(v)
            else:
                v = st.number_input(label, value=float(raw_num), key=widget_key)
                data[f.FieldName] = float(v)

            if f.Mandatory and data[f.FieldName] is None:
                errors.append(f"{f.FieldName} is mandatory")

        elif f.FieldType == "bool":
            v = st.checkbox(label, value=bool(values.get(f.FieldName) or False), key=widget_key)
            data[f.FieldName] = bool(v)

        elif f.FieldType == "date":
            d0 = _parse_iso_date(values.get(f.FieldName))
            v = st.date_input(label, value=d0, key=widget_key)
            if v is None:
                data[f.FieldName] = None
            else:
                data[f.FieldName] = v.isoformat()
            if f.Mandatory and not data[f.FieldName]:
                errors.append(f"{f.FieldName} is mandatory")

        elif f.FieldType == "lookup":
            if not f.LookupId:
                st.warning(f"Field '{f.FieldName}' is lookup but has no LookupId")
                data[f.FieldName] = None
                continue

            values_list = lookup_service.list_values(f.LookupId)
            options = [None] + [lv.Id for lv in values_list]
            id_to_text = {lv.Id: lv.Value for lv in values_list}

            current = values.get(f.FieldName)
            try:
                current = int(current) if current is not None and current != "" else None
            except Exception:
                current = None

            selected = st.selectbox(
                label,
                options=options,
                index=options.index(current) if current in options else 0,
                format_func=lambda x: "(none)" if x is None else f"{id_to_text.get(x, x)} (#{x})",
                key=widget_key,
            )
            if f.Mandatory and selected is None:
                errors.append(f"{f.FieldName} is mandatory")
            data[f.FieldName] = selected

        elif f.FieldType == "foreign_key":
            target = (getattr(f, "TargetTableName", None) or "").strip()
            if not target:
                st.warning(f"Field '{f.FieldName}' is foreign_key but has no TargetTableName")
                data[f.FieldName] = None
                continue

            try:
                fk_rows = crud_service.list_rows(target, limit=1000).rows
            except Exception as e:
                st.error(f"Failed to load FK options from '{target}': {e}")
                data[f.FieldName] = None
                continue

            options = [None] + [int(r["Id"]) for r in fk_rows if r.get("Id") is not None]
            id_to_text = {int(r["Id"]): row_label(r) for r in fk_rows if r.get("Id") is not None}

            current = values.get(f.FieldName)
            try:
                current = int(current) if current is not None and current != "" else None
            except Exception:
                current = None

            selected = st.selectbox(
                label,
                options=options,
                index=options.index(current) if current in options else 0,
                format_func=lambda x: "(none)" if x is None else f"{id_to_text.get(int(x), x)} (#{x})",
                key=widget_key,
            )
            if f.Mandatory and selected is None:
                errors.append(f"{f.FieldName} is mandatory")
            data[f.FieldName] = selected

        else:
            st.info(f"Unsupported field type '{f.FieldType}' - rendering as text")
            v = st.text_input(label, value=str(values.get(f.FieldName) or ""), key=widget_key)
            if f.Mandatory and not v.strip():
                errors.append(f"{f.FieldName} is mandatory")
            data[f.FieldName] = v.strip() if v.strip() else None

    return data, errors

