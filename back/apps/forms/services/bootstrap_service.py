from __future__ import annotations

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from sqlalchemy import inspect

from apps.common.db.sqlalchemy import get_engine
from apps.forms.models import Form, FormField, FormFieldType
from apps.lookups.models import Lookup, LookupValue
from apps.menus.models import Menu, Permission
from apps.reports.models import Report, ReportField
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
        "name": "UserUserGroup",
        "table_name": "user_user_group",
        "fields": [
            ("user_id", FormFieldType.FOREIGN_KEY, True),
            ("usergroup_id", FormFieldType.FOREIGN_KEY, True),
        ],
    },
    {
        "name": "Menu",
        "table_name": "menu",
        "fields": [
            ("name", FormFieldType.STRING, True),
            ("parent_menu_id", FormFieldType.FOREIGN_KEY, False),
            ("form_id", FormFieldType.FOREIGN_KEY, False),
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
            ("type", FormFieldType.LOOKUP, True),
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
    {
        "name": "Report",
        "table_name": "report",
        "fields": [
            ("name", FormFieldType.STRING, True),
            ("description", FormFieldType.TEXT, False),
            ("base_form_id", FormFieldType.FOREIGN_KEY, True),
        ],
    },
    {
        "name": "ReportField",
        "table_name": "report_field",
        "fields": [
            ("report_id", FormFieldType.FOREIGN_KEY, True),
            ("form_id", FormFieldType.FOREIGN_KEY, True),
            ("form_field_id", FormFieldType.FOREIGN_KEY, True),
            ("display_order", FormFieldType.INTEGER, True),
            ("display_name", FormFieldType.STRING, False),
        ],
    },
]

SYSTEM_FIELD_OPTIONS = {
    ("user_user_group", "user_id"): {"foreign_key_table": "user", "foreign_key_field": "id"},
    ("user_user_group", "usergroup_id"): {"foreign_key_table": "user_group", "foreign_key_field": "id"},
    ("menu", "parent_menu_id"): {"foreign_key_table": "menu", "foreign_key_field": "id"},
    ("menu", "form_id"): {"foreign_key_table": "form", "foreign_key_field": "id"},
    ("form_field", "form_id"): {"foreign_key_table": "form", "foreign_key_field": "id"},
    ("form_field", "lookup_id"): {"foreign_key_table": "lookup", "foreign_key_field": "id"},
    ("permission", "menu_id"): {"foreign_key_table": "menu", "foreign_key_field": "id"},
    ("permission", "group_id"): {"foreign_key_table": "user_group", "foreign_key_field": "id"},
    ("lookup_value", "lookup_id"): {"foreign_key_table": "lookup", "foreign_key_field": "id"},
    ("report", "base_form_id"): {"foreign_key_table": "form", "foreign_key_field": "id"},
    ("report_field", "report_id"): {"foreign_key_table": "report", "foreign_key_field": "id"},
    ("report_field", "form_id"): {"foreign_key_table": "form", "foreign_key_field": "id"},
    ("report_field", "form_field_id"): {"foreign_key_table": "form_field", "foreign_key_field": "id"},
}


class BootstrapService:
    @classmethod
    @transaction.atomic
    def bootstrap(cls) -> None:
        root_group = cls._ensure_root_group()
        cls._ensure_root_user(root_group)
        lookup_by_name = cls._ensure_default_lookups()
        system_field_options = cls._build_system_field_options(lookup_by_name)
        form_by_table: dict[str, Form] = {}

        for form_definition in SYSTEM_FORM_DEFINITIONS:
            form = Form.objects.update_or_create(
                table_name=form_definition["table_name"],
                defaults={
                    "name": form_definition["name"],
                    "description": f"System form for {form_definition['name']}",
                    "is_system": True,
                },
            )[0]
            form_by_table[form.table_name] = form

            for index, (name, field_type, mandatory) in enumerate(form_definition["fields"]):
                field_options = system_field_options.get((form.table_name, name), {})
                FormField.objects.update_or_create(
                    form=form,
                    name=name,
                    defaults={
                        "type": field_type,
                        "mandatory": mandatory,
                        "unique": False,
                        "lookup_id": field_options.get("lookup_id"),
                        "foreign_key_table": field_options.get("foreign_key_table", ""),
                        "foreign_key_field": field_options.get("foreign_key_field", "id"),
                        "default_value": "",
                        "sort_order": index,
                        "is_system": True,
                    },
                )

        cls._ensure_system_menu_tree(root_group, form_by_table)
        cls._ensure_seed_reports()

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
    def _ensure_default_lookups() -> dict[str, Lookup]:
        boolean_lookup, _ = Lookup.objects.get_or_create(
            name="BooleanChoice",
            defaults={"description": "System lookup for true/false labels"},
        )
        LookupValue.objects.get_or_create(lookup=boolean_lookup, value="True")
        LookupValue.objects.get_or_create(lookup=boolean_lookup, value="False")

        field_type_lookup, _ = Lookup.objects.get_or_create(
            name="FieldType",
            defaults={"description": "Supported runtime field types"},
        )
        for value in [choice.value for choice in FormFieldType]:
            LookupValue.objects.get_or_create(lookup=field_type_lookup, value=value)

        return {
            "BooleanChoice": boolean_lookup,
            "FieldType": field_type_lookup,
        }

    @staticmethod
    def _build_system_field_options(lookup_by_name: dict[str, Lookup]) -> dict[tuple[str, str], dict[str, str | int]]:
        options: dict[tuple[str, str], dict[str, str | int]] = dict(SYSTEM_FIELD_OPTIONS)
        field_type_lookup = lookup_by_name.get("FieldType")
        if field_type_lookup:
            options[("form_field", "type")] = {"lookup_id": int(field_type_lookup.id)}
        return options

    @classmethod
    def _ensure_system_menu_tree(cls, root_group: UserGroup, form_by_table: dict[str, Form]) -> None:
        system_menu = cls._upsert_folder_menu(name="System", parent_menu=None, sort_order=0)

        users_parent = cls._upsert_folder_menu(name="Users", parent_menu=system_menu, sort_order=1)
        forms_parent = cls._upsert_folder_menu(name="Forms", parent_menu=system_menu, sort_order=3)
        reporting_parent = cls._upsert_folder_menu(name="Reporting", parent_menu=system_menu, sort_order=4)

        leaf_definitions = [
            ("Users", "user", users_parent, 1),
            ("Groups", "user_group", users_parent, 2),
            ("Group Members", "user_user_group", users_parent, 3),
            ("Group Permissions", "permission", users_parent, 4),
            ("Menus", "menu", system_menu, 2),
            ("Forms", "form", forms_parent, 1),
            ("Fields", "form_field", forms_parent, 2),
            ("Lookups", "lookup", forms_parent, 3),
            ("Lookup Values", "lookup_value", forms_parent, 4),
            ("Reports", "report", reporting_parent, 1),
            ("Report Fields", "report_field", reporting_parent, 2),
        ]

        for menu_name, form_table_name, parent_menu, sort_order in leaf_definitions:
            form = form_by_table[form_table_name]
            menu = cls._upsert_form_menu(
                name=menu_name,
                form=form,
                parent_menu=parent_menu,
                sort_order=sort_order,
            )
            cls._upsert_root_group_permission(root_group, menu)

        cls._upsert_root_group_permission(root_group, system_menu)
        cls._upsert_root_group_permission(root_group, users_parent)
        cls._upsert_root_group_permission(root_group, forms_parent)
        cls._upsert_root_group_permission(root_group, reporting_parent)

        generate_report_menu = cls._upsert_folder_menu(
            name="Generate Report",
            parent_menu=reporting_parent,
            sort_order=3,
        )
        cls._upsert_root_group_permission(root_group, generate_report_menu)

    @staticmethod
    def _ensure_seed_reports() -> None:
        inspector = inspect(get_engine())
        if not inspector.has_table("report") or not inspector.has_table("report_field"):
            return

        base_form = Form.objects.filter(table_name="user").first()
        permission_form = Form.objects.filter(table_name="permission").first()
        if not base_form or not permission_form:
            return

        report, _ = Report.objects.update_or_create(
            name="User Permissions Report",
            defaults={
                "description": "Displays user permissions",
                "base_form": base_form,
            },
        )

        target_fields: list[tuple[Form, str, int, str]] = [
            (base_form, "username", 1, "Username"),
            (permission_form, "can_view", 2, "Can View"),
            (permission_form, "can_insert", 3, "Can Insert"),
            (permission_form, "can_update", 4, "Can Update"),
            (permission_form, "can_delete", 5, "Can Delete"),
            (permission_form, "can_print", 6, "Can Print"),
        ]

        for form, field_name, display_order, display_name in target_fields:
            form_field = FormField.objects.filter(form=form, name=field_name).first()
            if not form_field:
                continue
            ReportField.objects.update_or_create(
                report=report,
                form_field=form_field,
                defaults={
                    "form": form,
                    "display_order": display_order,
                    "display_name": display_name,
                },
            )

    @staticmethod
    def _upsert_folder_menu(*, name: str, parent_menu: Menu | None, sort_order: int) -> Menu:
        menu = (
            Menu.objects.filter(name=name, parent_menu=parent_menu, form__isnull=True)
            .order_by("id")
            .first()
        )
        if menu:
            menu.sort_order = sort_order
            menu.is_system = True
            menu.save(update_fields=["sort_order", "is_system"])
            return menu
        return Menu.objects.create(
            name=name,
            parent_menu=parent_menu,
            form=None,
            sort_order=sort_order,
            is_system=True,
        )

    @staticmethod
    def _upsert_form_menu(*, name: str, form: Form, parent_menu: Menu, sort_order: int) -> Menu:
        menu = Menu.objects.filter(form=form).order_by("id").first()
        if menu:
            menu.name = name
            menu.parent_menu = parent_menu
            menu.sort_order = sort_order
            menu.is_system = True
            menu.save(update_fields=["name", "parent_menu", "sort_order", "is_system"])
            return menu
        return Menu.objects.create(
            name=name,
            parent_menu=parent_menu,
            form=form,
            sort_order=sort_order,
            is_system=True,
        )

    @staticmethod
    def _upsert_root_group_permission(root_group: UserGroup, menu: Menu) -> None:
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

