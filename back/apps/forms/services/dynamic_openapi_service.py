from __future__ import annotations

from typing import Any


def inject_dynamic_form_schemas(result: dict[str, Any], generator, request, public) -> dict[str, Any]:
    # Keep schema generation resilient even when DB is not reachable.
    try:
        from django.db import OperationalError, ProgrammingError
        from apps.forms.models import Form
    except Exception:
        return result

    try:
        forms = list(
            Form.objects.filter(is_system=False)
            .prefetch_related("fields")
            .order_by("name", "id")
        )
    except (OperationalError, ProgrammingError):
        return result
    except Exception:
        return result

    components = result.setdefault("components", {})
    schemas = components.setdefault("schemas", {})

    dynamic_index: list[dict[str, str]] = []
    for form in forms:
        base_name = _pascal_case(form.name or form.table_name)
        schema_name = base_name
        create_name = f"{base_name}Create"
        update_name = f"{base_name}Update"
        list_name = f"{base_name}List"

        properties: dict[str, Any] = {
            "id": {"type": "integer", "readOnly": True},
            "created_at": {"type": "string", "format": "date-time", "readOnly": True},
            "updated_at": {"type": "string", "format": "date-time", "readOnly": True},
        }
        create_properties: dict[str, Any] = {}
        create_required: list[str] = []

        for field in form.fields.all():
            field_schema = _field_schema(field.type)
            properties[field.name] = field_schema
            create_properties[field.name] = field_schema
            if field.mandatory:
                create_required.append(field.name)

        schemas[schema_name] = {
            "type": "object",
            "description": f"Dynamic runtime record for form '{form.name}' mapped to table '{form.table_name}'.",
            "properties": properties,
        }
        schemas[create_name] = {
            "type": "object",
            "description": f"Create payload for dynamic form '{form.name}'.",
            "properties": create_properties,
            "required": create_required,
        }
        schemas[update_name] = {
            "type": "object",
            "description": f"Update payload for dynamic form '{form.name}'.",
            "properties": {"id": {"type": "integer"}, **create_properties},
            "required": ["id"],
        }
        schemas[list_name] = {
            "type": "object",
            "description": f"List response payload for dynamic form '{form.name}'.",
            "properties": {
                "count": {"type": "integer"},
                "items": {"type": "array", "items": {"$ref": f"#/components/schemas/{schema_name}"}},
            },
            "required": ["count", "items"],
        }

        dynamic_index.append(
            {
                "name": form.name,
                "table": form.table_name,
                "schema": schema_name,
                "create": create_name,
                "update": update_name,
                "list": list_name,
            }
        )

    result["x-dynamic-forms"] = dynamic_index
    return result


def _field_schema(field_type: str) -> dict[str, Any]:
    mapping = {
        "Integer": {"type": "integer"},
        "Double": {"type": "number", "format": "double"},
        "Decimal": {"type": "number", "format": "decimal"},
        "String": {"type": "string"},
        "Text": {"type": "string"},
        "Date": {"type": "string", "format": "date"},
        "DateTime": {"type": "string", "format": "date-time"},
        "Boolean": {"type": "boolean"},
        "Lookup": {"type": "integer"},
        "ForeignKey": {"type": "integer"},
    }
    return mapping.get(field_type, {"type": "string"})


def _pascal_case(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else " " for ch in value)
    tokens = [token for token in cleaned.split() if token]
    if not tokens:
        return "DynamicForm"
    return "".join(token[:1].upper() + token[1:] for token in tokens)

