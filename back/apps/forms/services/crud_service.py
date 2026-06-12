from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from django.conf import settings
from django.forms.models import model_to_dict
from sqlalchemy import MetaData, Table, and_, delete, func, inspect, insert, or_, select, update

from apps.common.db.sqlalchemy import get_engine
from apps.common.exceptions import NotFoundException, ValidationException
from apps.common.permissions.permission_service import PermissionService
from apps.forms.models import Form, FormField
from apps.forms.services.filter_parser import FilterParser
from apps.forms.services.validation_service import ValidationService
from apps.lookups.models import Lookup, LookupValue
from apps.menus.models import Menu, Permission
from apps.users.models import User, UserGroup


SYSTEM_MODELS = {
    "user": User,
    "user_group": UserGroup,
    "menu": Menu,
    "form": Form,
    "form_field": FormField,
    "permission": Permission,
    "lookup": Lookup,
    "lookup_value": LookupValue,
}

PROTECTED_TABLES = {"form", "form_field", "menu", "permission"}


@dataclass
class ListResult:
    count: int
    items: list[dict[str, Any]]


class CrudService:
    @classmethod
    def list_options(
        cls,
        *,
        user,
        table_name: str,
        query: str = "",
        ids: list[int] | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        PermissionService.assert_table_permission(user, table_name, "list")
        form = ValidationService.get_form_or_raise(table_name)
        table = cls._get_dynamic_table(form)

        label_field_name = cls._resolve_label_field_name(form, table)
        label_column = table.c[label_field_name]

        sql = select(table.c.id, label_column.label("label"))
        if ids:
            sql = sql.where(table.c.id.in_(ids))
        elif query.strip():
            query_value = query.strip()
            string_like = {"String", "Text"}
            if label_field_name == "id":
                if query_value.isdigit():
                    sql = sql.where(table.c.id == int(query_value))
                else:
                    return []
            else:
                label_type = next((f.type for f in form.fields.all() if f.name == label_field_name), None)
                if label_type in string_like:
                    sql = sql.where(label_column.ilike(f"%{query_value}%"))
                elif query_value.isdigit():
                    sql = sql.where(or_(table.c.id == int(query_value), label_column == int(query_value)))
                else:
                    sql = sql.where(table.c.id == -1)

        sql = sql.order_by(table.c.id.asc()).limit(limit)

        engine = get_engine()
        with engine.begin() as connection:
            rows = connection.execute(sql).mappings().all()

        return [
            {
                "id": int(row["id"]),
                "label": str(row["label"]) if row["label"] is not None else str(row["id"]),
            }
            for row in rows
        ]

    @classmethod
    def insert(cls, *, user, table_name: str, data: dict) -> dict:
        PermissionService.assert_table_permission(user, table_name, "insert")
        data = cls._normalize_payload(table_name, data, is_update=False)
        form = ValidationService.get_form_or_raise(table_name)
        ValidationService.validate_payload(form, data, is_update=False)

        if form.is_system and table_name in SYSTEM_MODELS:
            return cls._insert_system(table_name, data)
        return cls._insert_dynamic(form, data)

    @classmethod
    def update(cls, *, user, table_name: str, data: dict) -> dict:
        PermissionService.assert_table_permission(user, table_name, "update")
        data = cls._normalize_payload(table_name, data, is_update=True)
        if "id" not in data:
            raise ValidationException("id is required for update", field="id")

        form = ValidationService.get_form_or_raise(table_name)
        ValidationService.validate_payload(form, data, is_update=True)

        if form.is_system and table_name in SYSTEM_MODELS:
            return cls._update_system(table_name, data)
        return cls._update_dynamic(form, data)

    @classmethod
    def delete(cls, *, user, table_name: str, data: dict) -> None:
        PermissionService.assert_table_permission(user, table_name, "delete")
        record_id = data.get("id")
        if not record_id:
            raise ValidationException("id is required for delete", field="id")

        form = ValidationService.get_form_or_raise(table_name)
        if form.is_system and table_name in SYSTEM_MODELS:
            cls._delete_system(table_name, int(record_id))
            return
        cls._delete_dynamic(form, int(record_id))

    @classmethod
    def detail(cls, *, user, table_name: str, record_id: int) -> dict:
        PermissionService.assert_table_permission(user, table_name, "detail")
        form = ValidationService.get_form_or_raise(table_name)
        if form.is_system and table_name in SYSTEM_MODELS:
            model = SYSTEM_MODELS[table_name]
            instance = model.objects.filter(pk=record_id).first()
            if not instance:
                raise NotFoundException("Record not found")
            return cls._model_to_row(instance)
        return cls._detail_dynamic(form, record_id)

    @classmethod
    def list(cls, *, user, table_name: str, limit: int, offset: int, sort_by: str, sort_direction: str, filters: dict) -> ListResult:
        PermissionService.assert_table_permission(user, table_name, "list")
        form = ValidationService.get_form_or_raise(table_name)
        if form.is_system and table_name in SYSTEM_MODELS:
            return cls._list_system(table_name, limit, offset, sort_by, sort_direction, filters)
        return cls._list_dynamic(form, limit, offset, sort_by, sort_direction, filters)

    @classmethod
    def _insert_system(cls, table_name: str, data: dict) -> dict:
        model = SYSTEM_MODELS[table_name]
        if table_name == "user":
            username = data.get("username")
            password = data.get("password")
            if not username or not password:
                raise ValidationException("username and password are required")
            instance = model.objects.create_user(username=username, password=password, is_active=data.get("is_active", True))
            groups = data.get("groups_ref") or []
            if groups:
                instance.groups_ref.set(UserGroup.objects.filter(id__in=groups))
            return cls._model_to_row(instance)

        instance = model.objects.create(**data)
        return cls._model_to_row(instance)

    @classmethod
    def _update_system(cls, table_name: str, data: dict) -> dict:
        model = SYSTEM_MODELS[table_name]
        instance = model.objects.filter(pk=data["id"]).first()
        if not instance:
            raise NotFoundException("Record not found")

        if table_name in PROTECTED_TABLES and getattr(instance, "is_system", False):
            raise ValidationException("System metadata cannot be modified")
        if table_name == "permission" and instance.group.name == settings.HRMS["ROOT_GROUP_NAME"]:
            raise ValidationException("Protected permissions cannot be modified")

        if table_name == "user" and instance.username == settings.HRMS["ROOT_USERNAME"] and data.get("is_active") is False:
            raise ValidationException("Root administrator cannot be deactivated")

        for key, value in data.items():
            if key == "id":
                continue
            if table_name == "user" and key == "password":
                instance.set_password(value)
                continue
            if table_name == "user" and key == "groups_ref":
                instance.groups_ref.set(UserGroup.objects.filter(id__in=value or []))
                continue
            setattr(instance, key, value)
        instance.save()
        return cls._model_to_row(instance)

    @classmethod
    def _delete_system(cls, table_name: str, record_id: int) -> None:
        model = SYSTEM_MODELS[table_name]
        instance = model.objects.filter(pk=record_id).first()
        if not instance:
            raise NotFoundException("Record not found")

        if table_name == "user" and instance.username == settings.HRMS["ROOT_USERNAME"]:
            raise ValidationException("Root administrator cannot be deleted")
        if table_name == "user_group" and instance.name == settings.HRMS["ROOT_GROUP_NAME"]:
            raise ValidationException("Root administrator group cannot be deleted")
        if table_name == "permission" and instance.group.name == settings.HRMS["ROOT_GROUP_NAME"]:
            raise ValidationException("Protected permissions cannot be deleted")
        if table_name in {"form", "form_field", "menu"} and getattr(instance, "is_system", False):
            raise ValidationException("System resources cannot be deleted")

        instance.delete()

    @classmethod
    def _list_system(cls, table_name: str, limit: int, offset: int, sort_by: str, sort_direction: str, filters: dict) -> ListResult:
        model = SYSTEM_MODELS[table_name]
        qs = model.objects.all()
        field_by_name = {
            field.name: field
            for field in model._meta.get_fields()
            if getattr(field, "concrete", False)
        }
        allowed_fields = set()
        for field in model._meta.get_fields():
            if getattr(field, "many_to_many", False):
                allowed_fields.add(field.name)
                continue
            if getattr(field, "concrete", False):
                allowed_fields.add(field.name)
                attname = getattr(field, "attname", None)
                if attname:
                    allowed_fields.add(attname)

        if sort_by not in allowed_fields:
            raise ValidationException("Invalid sort column", field="sort_by")

        expression_like = any(
            isinstance(value, str) and any(token in value for token in ("&", "|", "(", ")", ">", "<", "!=", "="))
            for value in (filters or {}).values()
        )
        if expression_like:
            form = ValidationService.get_form_or_raise(table_name)
            normalized_sort_by = cls._normalize_system_column_name(field_by_name, sort_by)
            normalized_filters = {
                cls._normalize_system_column_name(field_by_name, key): value
                for key, value in (filters or {}).items()
            }
            return cls._list_dynamic(form, limit, offset, normalized_sort_by, sort_direction, normalized_filters)

        if filters:
            for key, value in filters.items():
                if key not in allowed_fields:
                    raise ValidationException("Unknown filter field", field=key)
                qs = qs.filter(**{key: value})

        if sort_direction == "desc":
            qs = qs.order_by(f"-{sort_by}")
        else:
            qs = qs.order_by(sort_by)

        count = qs.count()
        items = [cls._model_to_row(obj) for obj in qs[offset : offset + limit]]
        return ListResult(count=count, items=items)

    @staticmethod
    def _normalize_system_column_name(field_by_name: dict[str, Any], key: str) -> str:
        field = field_by_name.get(key)
        if field is None:
            return key
        return getattr(field, "attname", key) or key

    @staticmethod
    def _model_to_row(instance) -> dict:
        payload = model_to_dict(instance)
        for field in instance._meta.fields:
            if getattr(field, "is_relation", False) and getattr(field, "many_to_one", False):
                payload[field.attname] = getattr(instance, field.attname)
                payload.pop(field.name, None)
        payload["id"] = instance.id
        return payload

    @classmethod
    def _normalize_payload(cls, table_name: str, data: dict, is_update: bool) -> dict:
        payload = dict(data)
        if table_name != "form_field":
            return payload

        foreign_key_form = payload.pop("foreign_key_form", None)
        field_type = payload.get("type")

        if foreign_key_form is not None:
            if field_type and field_type != "ForeignKey":
                raise ValidationException("foreign_key_form is only valid for ForeignKey fields", field="foreign_key_form")
            referenced_form = (
                Form.objects.filter(name=foreign_key_form).order_by("id").first()
                or Form.objects.filter(table_name=foreign_key_form).order_by("id").first()
            )
            if not referenced_form:
                raise ValidationException("Unknown foreign key form", field="foreign_key_form")
            payload["foreign_key_table"] = referenced_form.table_name

        # Keep foreign_key_field optional; id is the default target.
        if payload.get("type") == "ForeignKey" and not payload.get("foreign_key_field"):
            payload["foreign_key_field"] = "id"

        return payload

    @classmethod
    def _get_dynamic_table(cls, form: Form) -> Table:
        engine = get_engine()
        inspector = inspect(engine)
        if not inspector.has_table(form.table_name):
            raise NotFoundException("Physical table does not exist")
        metadata = MetaData()
        return Table(form.table_name, metadata, autoload_with=engine)

    @staticmethod
    def _resolve_label_field_name(form: Form, table: Table) -> str:
        preferred_types = {"String", "Text"}
        sorted_fields = sorted(form.fields.all(), key=lambda field: (field.sort_order, field.id))
        for field in sorted_fields:
            if field.name in {"id", "created_at", "updated_at", "password_hash"}:
                continue
            if field.type in preferred_types and field.name in table.c:
                return field.name
        for field in sorted_fields:
            if field.name in table.c and field.name not in {"id", "password_hash"}:
                return field.name
        return "id"

    @classmethod
    def _insert_dynamic(cls, form: Form, data: dict) -> dict:
        table = cls._get_dynamic_table(form)
        engine = get_engine()
        payload = {k: v for k, v in data.items() if k in table.c.keys() and k != "id"}
        with engine.begin() as connection:
            result = connection.execute(insert(table).values(**payload).returning(*table.columns))
            row = result.mappings().first()
        return dict(row)

    @classmethod
    def _update_dynamic(cls, form: Form, data: dict) -> dict:
        table = cls._get_dynamic_table(form)
        engine = get_engine()
        record_id = data["id"]
        payload = {k: v for k, v in data.items() if k in table.c.keys() and k != "id"}
        with engine.begin() as connection:
            result = connection.execute(
                update(table).where(table.c.id == record_id).values(**payload).returning(*table.columns)
            )
            row = result.mappings().first()
            if not row:
                raise NotFoundException("Record not found")
        return dict(row)

    @classmethod
    def _delete_dynamic(cls, form: Form, record_id: int) -> None:
        table = cls._get_dynamic_table(form)
        engine = get_engine()
        with engine.begin() as connection:
            result = connection.execute(delete(table).where(table.c.id == record_id))
            if result.rowcount == 0:
                raise NotFoundException("Record not found")

    @classmethod
    def _detail_dynamic(cls, form: Form, record_id: int) -> dict:
        table = cls._get_dynamic_table(form)
        engine = get_engine()
        with engine.begin() as connection:
            result = connection.execute(select(table).where(table.c.id == record_id).limit(1))
            row = result.mappings().first()
        if not row:
            raise NotFoundException("Record not found")
        return dict(row)

    @classmethod
    def _list_dynamic(cls, form: Form, limit: int, offset: int, sort_by: str, sort_direction: str, filters: dict) -> ListResult:
        table = cls._get_dynamic_table(form)
        fields_map = ValidationService.get_form_fields_map(form)

        if sort_by not in table.c.keys():
            raise ValidationException("Invalid sort column", field="sort_by")
        sort_column = table.c[sort_by]
        order_clause = sort_column.desc() if sort_direction == "desc" else sort_column.asc()

        predicates = []
        for field_name, expression in (filters or {}).items():
            form_field = fields_map.get(field_name)
            if not form_field:
                raise ValidationException("Unknown filter field", field=field_name)
            filter_expr = FilterParser.parse(field_name, form_field.type, str(expression), table.c[field_name])
            if filter_expr is not None:
                predicates.append(filter_expr)

        base_query = select(table)
        count_query = select(func.count()).select_from(table)
        if predicates:
            predicate = and_(*predicates)
            base_query = base_query.where(predicate)
            count_query = count_query.where(predicate)

        base_query = base_query.order_by(order_clause).limit(limit).offset(offset)

        engine = get_engine()
        with engine.begin() as connection:
            count = connection.execute(count_query).scalar_one()
            rows = connection.execute(base_query).mappings().all()

        return ListResult(count=count, items=[dict(row) for row in rows])







