from __future__ import annotations

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.forms.models import Form, FormField, FormFieldType
from apps.lookups.models import Lookup, LookupValue
from apps.menus.models import Menu, Permission
from apps.users.models import UserGroup


SYSTEM_FORM_DEFINITIONS = [
    {
        "name": "User",
        "table_name": "user",
        "fields": [
            ("username", FormFieldType.STRING, True),
            ("password_hash", FormFieldType.STRING, True),
            ("is_active", FormFieldType.BOOLEAN, True),
            ("created_at", FormFieldType.DATETIME, True),
            ("updated_at", FormFieldType.DATETIME, True),
        ],
    },
    {
        "name": "UserGroup",
        "table_name": "user_group",
        "fields": [
            ("name", FormFieldType.STRING, True),
            ("description", FormFieldType.TEXT, False),
        ],
    },
    {
        "name": "Menu",
        "table_name": "menu",
        "fields": [
            ("name", FormFieldType.STRING, True),
            ("parent_menu_id", FormFieldType.FOREIGN_KEY, False),
            ("form_id", FormFieldType.FOREIGN_KEY, True),
            ("sort_order", FormFieldType.INTEGER, False),
            ("is_system", FormFieldType.BOOLEAN, True),
        ],
    },
    {
        "name": "Form",
        "table_name": "form",
        "fields": [
            ("name", FormFieldType.STRING, True),
            ("description", FormFieldType.TEXT, False),
            ("table_name", FormFieldType.STRING, True),
            ("is_system", FormFieldType.BOOLEAN, True),
            ("created_at", FormFieldType.DATETIME, True),
            ("updated_at", FormFieldType.DATETIME, True),
        ],
    },
    {
        "name": "FormField",
        "table_name": "form_field",
        "fields": [
            ("form_id", FormFieldType.FOREIGN_KEY, True),
            ("name", FormFieldType.STRING, True),
            ("type", FormFieldType.STRING, True),
            ("mandatory", FormFieldType.BOOLEAN, True),
            ("unique", FormFieldType.BOOLEAN, True),
            ("lookup_id", FormFieldType.FOREIGN_KEY, False),
            ("foreign_key_table", FormFieldType.STRING, False),
            ("foreign_key_field", FormFieldType.STRING, False),
            ("default_value", FormFieldType.STRING, False),
            ("sort_order", FormFieldType.INTEGER, False),
            ("is_system", FormFieldType.BOOLEAN, True),
        ],
    },
    {
        "name": "Permission",
        "table_name": "permission",
        "fields": [
            ("menu_id", FormFieldType.FOREIGN_KEY, True),
            ("group_id", FormFieldType.FOREIGN_KEY, True),
            ("can_view", FormFieldType.BOOLEAN, True),
            ("can_insert", FormFieldType.BOOLEAN, True),
            ("can_update", FormFieldType.BOOLEAN, True),
            ("can_delete", FormFieldType.BOOLEAN, True),
            ("can_print", FormFieldType.BOOLEAN, True),
        ],
    },
    {
        "name": "Lookup",
        "table_name": "lookup",
        "fields": [
            ("name", FormFieldType.STRING, True),
            ("description", FormFieldType.TEXT, False),
        ],
    },
    {
        "name": "LookupValue",
        "table_name": "lookup_value",
        "fields": [
            ("lookup_id", FormFieldType.FOREIGN_KEY, True),
            ("value", FormFieldType.STRING, True),
        ],
    },
]


class BootstrapService:
    @classmethod
    @transaction.atomic
    def bootstrap(cls) -> None:
        root_group = cls._ensure_root_group()
        cls._ensure_root_user(root_group)

        for form_definition in SYSTEM_FORM_DEFINITIONS:
            form = Form.objects.update_or_create(
                table_name=form_definition["table_name"],
                defaults={
                    "name": form_definition["name"],
                    "description": f"System form for {form_definition['name']}",
                    "is_system": True,
                },
            )[0]

            for index, (name, field_type, mandatory) in enumerate(form_definition["fields"]):
                FormField.objects.update_or_create(
                    form=form,
                    name=name,
                    defaults={
                        "type": field_type,
                        "mandatory": mandatory,
                        "unique": False,
                        "sort_order": index,
                        "is_system": True,
                    },
                )

            menu = Menu.objects.update_or_create(
                form=form,
                defaults={
                    "name": form_definition["name"],
                    "sort_order": 0,
                    "is_system": True,
                },
            )[0]

            Permission.objects.update_or_create(
                menu=menu,
                group=root_group,
                defaults={
                    "can_view": True,
                    "can_insert": True,
                    "can_update": True,
                    "can_delete": True,
                    "can_print": True,
                },
            )

        cls._ensure_default_lookups()

    @staticmethod
    def _ensure_root_group() -> UserGroup:
        group_name = settings.HRMS["ROOT_GROUP_NAME"]
        group, _ = UserGroup.objects.get_or_create(
            name=group_name,
            defaults={"description": "Protected root administrator group"},
        )
        return group

    @staticmethod
    def _ensure_root_user(root_group: UserGroup) -> None:
        user_model = get_user_model()
        root_username = settings.HRMS["ROOT_USERNAME"]
        root_password = settings.HRMS["ROOT_PASSWORD"]
        user, created = user_model.objects.get_or_create(
            username=root_username,
            defaults={"is_superuser": True, "is_staff": True, "is_active": True},
        )
        if created:
            user.set_password(root_password)
            user.save(update_fields=["password"])
        user.groups_ref.add(root_group)

    @staticmethod
    def _ensure_default_lookups() -> None:
        boolean_lookup, _ = Lookup.objects.get_or_create(
            name="BooleanChoice",
            defaults={"description": "System lookup for true/false labels"},
        )
        LookupValue.objects.get_or_create(lookup=boolean_lookup, value="True")
        LookupValue.objects.get_or_create(lookup=boolean_lookup, value="False")

