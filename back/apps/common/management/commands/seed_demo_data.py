from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from sqlalchemy import MetaData, Table, delete, func, inspect, select

from apps.common.db.sqlalchemy import get_engine
from apps.forms.models import Form, FormField, FormFieldType
from apps.forms.services.schema_service import SchemaService
from apps.lookups.models import Lookup, LookupValue
from apps.menus.models import Menu, Permission
from apps.users.models import UserGroup


@dataclass(frozen=True)
class FieldDefinition:
    name: str
    field_type: str
    mandatory: bool = False
    unique: bool = False
    lookup_name: str = ""
    foreign_key_table: str = ""
    foreign_key_field: str = "id"
    default_value: str = ""


FORM_DEFINITIONS: list[dict] = [
    {
        "name": "Organization Unit",
        "table_name": "organization_unit",
        "description": "Organizational units and hierarchy",
        "fields": [
            FieldDefinition(name="name", field_type=FormFieldType.STRING, mandatory=True),
            FieldDefinition(name="description", field_type=FormFieldType.STRING, mandatory=False),
            FieldDefinition(
                name="parent_organization_id",
                field_type=FormFieldType.FOREIGN_KEY,
                mandatory=False,
                foreign_key_table="organization_unit",
            ),
        ],
    },
    {
        "name": "Employee",
        "table_name": "employee",
        "description": "Employee master records",
        "fields": [
            FieldDefinition(name="first_name", field_type=FormFieldType.STRING, mandatory=True),
            FieldDefinition(name="last_name", field_type=FormFieldType.STRING, mandatory=True),
            FieldDefinition(name="father_name", field_type=FormFieldType.STRING, mandatory=False),
            FieldDefinition(name="national_code", field_type=FormFieldType.STRING, mandatory=True, unique=True),
            FieldDefinition(name="birth_date", field_type=FormFieldType.DATE, mandatory=True),
            FieldDefinition(name="birth_city", field_type=FormFieldType.LOOKUP, mandatory=False, lookup_name="City"),
            FieldDefinition(
                name="organization_id",
                field_type=FormFieldType.FOREIGN_KEY,
                mandatory=False,
                foreign_key_table="organization_unit",
            ),
        ],
    },
    {
        "name": "Dependent",
        "table_name": "dependent",
        "description": "Employee dependents",
        "fields": [
            FieldDefinition(
                name="employee_id",
                field_type=FormFieldType.FOREIGN_KEY,
                mandatory=True,
                foreign_key_table="employee",
            ),
            FieldDefinition(name="first_name", field_type=FormFieldType.STRING, mandatory=True),
            FieldDefinition(name="last_name", field_type=FormFieldType.STRING, mandatory=True),
            FieldDefinition(name="national_code", field_type=FormFieldType.STRING, mandatory=True, unique=True),
            FieldDefinition(name="relation_type", field_type=FormFieldType.LOOKUP, mandatory=False, lookup_name="Relation"),
        ],
    },
    {
        "name": "Contract",
        "table_name": "contract",
        "description": "Employee contracts",
        "fields": [
            FieldDefinition(
                name="employee_id",
                field_type=FormFieldType.FOREIGN_KEY,
                mandatory=True,
                foreign_key_table="employee",
            ),
            FieldDefinition(name="from_date", field_type=FormFieldType.DATE, mandatory=True),
            FieldDefinition(name="to_date", field_type=FormFieldType.DATE, mandatory=False),
            FieldDefinition(name="contract_type", field_type=FormFieldType.LOOKUP, mandatory=False, lookup_name="Contract"),
            FieldDefinition(name="secretariat_number", field_type=FormFieldType.STRING, mandatory=True),
            FieldDefinition(name="issue_date", field_type=FormFieldType.DATE, mandatory=False),
            FieldDefinition(name="registration_date", field_type=FormFieldType.DATE, mandatory=False),
        ],
    },
    {
        "name": "Hokm",
        "table_name": "hokm",
        "description": "Employee hokm records",
        "fields": [
            FieldDefinition(
                name="employee_id",
                field_type=FormFieldType.FOREIGN_KEY,
                mandatory=True,
                foreign_key_table="employee",
            ),
            FieldDefinition(name="calculation_date", field_type=FormFieldType.DATE, mandatory=True),
            FieldDefinition(name="execution_date", field_type=FormFieldType.DATE, mandatory=False),
        ],
    },
    {
        "name": "Internal Experience",
        "table_name": "internal_experience",
        "description": "Internal employee experiences",
        "fields": [
            FieldDefinition(
                name="employee_id",
                field_type=FormFieldType.FOREIGN_KEY,
                mandatory=True,
                foreign_key_table="employee",
            ),
            FieldDefinition(name="from_date", field_type=FormFieldType.DATE, mandatory=True),
            FieldDefinition(name="to_date", field_type=FormFieldType.DATE, mandatory=False),
            FieldDefinition(name="education_degree", field_type=FormFieldType.LOOKUP, mandatory=False, lookup_name="Education"),
            FieldDefinition(name="field_of_study", field_type=FormFieldType.STRING, mandatory=False),
            FieldDefinition(name="employment_type", field_type=FormFieldType.LOOKUP, mandatory=False, lookup_name="Contract"),
            FieldDefinition(name="job_title", field_type=FormFieldType.STRING, mandatory=False),
            FieldDefinition(name="work_city", field_type=FormFieldType.LOOKUP, mandatory=False, lookup_name="City"),
            FieldDefinition(
                name="employment_status",
                field_type=FormFieldType.LOOKUP,
                mandatory=False,
                lookup_name="EmploymentStatus",
            ),
        ],
    },
    {
        "name": "External Experience",
        "table_name": "external_experience",
        "description": "External employee experiences",
        "fields": [
            FieldDefinition(
                name="employee_id",
                field_type=FormFieldType.FOREIGN_KEY,
                mandatory=True,
                foreign_key_table="employee",
            ),
            FieldDefinition(name="from_date", field_type=FormFieldType.DATE, mandatory=True),
            FieldDefinition(name="to_date", field_type=FormFieldType.DATE, mandatory=True),
            FieldDefinition(name="education_degree", field_type=FormFieldType.LOOKUP, mandatory=False, lookup_name="Education"),
            FieldDefinition(name="field_of_study", field_type=FormFieldType.STRING, mandatory=False),
            FieldDefinition(name="employment_type", field_type=FormFieldType.LOOKUP, mandatory=False, lookup_name="Contract"),
            FieldDefinition(name="job_title", field_type=FormFieldType.STRING, mandatory=False),
        ],
    },
]

LOOKUP_DEFINITIONS: dict[str, list[str]] = {
    "City": ["Tehran", "Sari", "Isfahan", "Shiraz"],
    "Education": ["BSc", "MSc", "PhD"],
    "Contract": ["Part-time", "Full-time", "Out-source"],
    "EmploymentStatus": ["Active", "Promoted", "Demoted", "Fired"],
    "Relation": ["Spouse", "Child"],
}

SYSTEM_MENU_TREE = {
    "System": {
        "Users": ["Users", "Groups", "Group Members", "Group Permissions"],
        "_items": ["Menus", "Forms"],
        "Forms": ["Forms", "Fields", "Lookups", "Lookup Values"],
    }
}

HR_MENU_TREE = {
    "Human Resources": {
        "_items": ["Organization Units", "Employees"],
        "Employee Affairs": ["Dependents", "Contracts", "Hokm"],
        "Experiences": ["Internal Experiences", "External Experiences"],
    }
}

MENU_TO_FORM_TABLE: dict[str, str] = {
    "Organization Units": "organization_unit",
    "Employees": "employee",
    "Dependents": "dependent",
    "Contracts": "contract",
    "Hokm": "hokm",
    "Internal Experiences": "internal_experience",
    "External Experiences": "external_experience",
}

GROUP_DEFINITIONS: list[tuple[str, str]] = [
    ("HR Managers", "Human resources managers"),
    ("HR Experts", "Human resources specialists"),
    ("Auditors", "Read-only audit users"),
]


class Command(BaseCommand):
    help = "Seed HRMS demo metadata and mock data."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--reset-demo-data",
            action="store_true",
            help="Delete existing demo rows from generated dynamic business tables before reseeding.",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=1405,
            help="Random seed for deterministic output.",
        )

    def handle(self, *args, **options):
        if not self._is_runtime_ready():
            raise CommandError("Run migrations first. Required core metadata tables do not exist.")

        rng = random.Random(options["seed"])
        self.stdout.write(self.style.NOTICE(f"Starting demo seed (seed={options['seed']}) ..."))

        summary: dict[str, dict[str, int]] = {
            "menus": {},
            "forms": {},
            "lookups": {},
            "permissions": {},
            "records": {},
        }

        with transaction.atomic():
            lookup_map = self._ensure_lookups(summary)
            form_map = self._ensure_forms_and_fields(lookup_map, summary)
            self._ensure_physical_tables_and_columns(form_map)
            menu_map = self._ensure_menu_hierarchy(form_map, summary)
            self._ensure_demo_groups_and_users(summary)
            self._ensure_permissions_and_security(menu_map, summary)

        # Dynamic data should be outside the atomic block because SQLAlchemy DML and Django ORM
        # share the same DB but not the same transaction manager lifecycle.
        if options["reset_demo_data"]:
            self._reset_dynamic_demo_data()

        self._seed_business_data(form_map, lookup_map, rng, summary)
        self._print_summary(summary, options["seed"])
        self.stdout.write(self.style.SUCCESS("Demo seed completed successfully."))

    @staticmethod
    def _is_runtime_ready() -> bool:
        engine = get_engine()
        inspector = inspect(engine)
        required = {"form", "form_field", "menu", "permission", "lookup", "lookup_value", "user_group", "user"}
        return required.issubset(set(inspector.get_table_names()))

    def _ensure_lookups(self, summary: dict[str, dict[str, int]]) -> dict[str, dict[str, int]]:
        self.stdout.write("Ensuring lookup definitions ...")
        lookup_map: dict[str, dict[str, int]] = {}
        created_lookups = 0
        created_values = 0
        for lookup_name, values in LOOKUP_DEFINITIONS.items():
            lookup, created = Lookup.objects.get_or_create(
                name=lookup_name,
                defaults={"description": f"{lookup_name} lookup values"},
            )
            if created:
                created_lookups += 1
            lookup_map[lookup_name] = {}
            for value in values:
                lookup_value, value_created = LookupValue.objects.get_or_create(lookup=lookup, value=value)
                if value_created:
                    created_values += 1
                lookup_map[lookup_name][value] = int(lookup_value.id)

        summary["lookups"]["lookup_types_created"] = created_lookups
        summary["lookups"]["lookup_values_created"] = created_values
        summary["lookups"]["lookup_types_total"] = len(LOOKUP_DEFINITIONS)
        summary["lookups"]["lookup_values_total"] = sum(len(v) for v in LOOKUP_DEFINITIONS.values())
        return lookup_map

    def _ensure_forms_and_fields(
        self, lookup_map: dict[str, dict[str, int]], summary: dict[str, dict[str, int]]
    ) -> dict[str, Form]:
        self.stdout.write("Ensuring form and field metadata ...")
        created_forms = 0
        created_fields = 0
        form_map: dict[str, Form] = {}

        for form_def in FORM_DEFINITIONS:
            form, created = Form.objects.update_or_create(
                table_name=form_def["table_name"],
                defaults={
                    "name": form_def["name"],
                    "description": form_def["description"],
                    "is_system": False,
                },
            )
            if created:
                created_forms += 1
            form_map[form.table_name] = form

            for sort_order, field_def in enumerate(form_def["fields"], start=1):
                lookup_id = None
                if field_def.lookup_name:
                    lookup = Lookup.objects.filter(name=field_def.lookup_name).first()
                    lookup_id = lookup.id if lookup else None
                    if lookup_id is None:
                        raise CommandError(f"Missing lookup '{field_def.lookup_name}' for field '{field_def.name}'.")

                _, field_created = FormField.objects.update_or_create(
                    form=form,
                    name=field_def.name,
                    defaults={
                        "type": field_def.field_type,
                        "mandatory": field_def.mandatory,
                        "unique": field_def.unique,
                        "lookup_id": lookup_id,
                        "foreign_key_table": field_def.foreign_key_table,
                        "foreign_key_field": field_def.foreign_key_field,
                        "default_value": field_def.default_value,
                        "sort_order": sort_order,
                        "is_system": False,
                    },
                )
                if field_created:
                    created_fields += 1

        summary["forms"]["forms_created"] = created_forms
        summary["forms"]["form_fields_created"] = created_fields
        summary["forms"]["forms_total"] = len(FORM_DEFINITIONS)
        summary["forms"]["form_fields_total"] = sum(len(form["fields"]) for form in FORM_DEFINITIONS)
        return form_map

    def _ensure_physical_tables_and_columns(self, form_map: dict[str, Form]) -> None:
        self.stdout.write("Ensuring physical tables and columns for demo forms ...")
        engine = get_engine()
        inspector = inspect(engine)
        for form in form_map.values():
            if not inspector.has_table(form.table_name):
                SchemaService.create_dynamic_table(form)

            refreshed_inspector = inspect(engine)
            if not refreshed_inspector.has_table(form.table_name):
                raise CommandError(f"Failed to create physical table '{form.table_name}'.")

            existing_columns = {column["name"] for column in refreshed_inspector.get_columns(form.table_name)}
            for field in form.fields.order_by("sort_order", "id"):
                if field.name not in existing_columns:
                    SchemaService.add_field(form, field)
                    existing_columns.add(field.name)

    def _ensure_menu_hierarchy(self, form_map: dict[str, Form], summary: dict[str, dict[str, int]]) -> dict[str, Menu]:
        self.stdout.write("Ensuring menu hierarchy ...")
        menu_map: dict[str, Menu] = {}
        created_count = 0

        created_count += self._upsert_tree(SYSTEM_MENU_TREE, parent_menu=None, form_map=form_map, menu_map=menu_map)
        created_count += self._upsert_tree(HR_MENU_TREE, parent_menu=None, form_map=form_map, menu_map=menu_map)

        summary["menus"]["menus_created"] = created_count
        summary["menus"]["menus_total_target"] = len(menu_map)
        return menu_map

    def _upsert_tree(
        self,
        tree: dict,
        *,
        parent_menu: Menu | None,
        form_map: dict[str, Form],
        menu_map: dict[str, Menu],
    ) -> int:
        created_count = 0
        for idx, (node_name, children) in enumerate(tree.items(), start=1):
            node_menu, created = self._upsert_folder_menu(name=node_name, parent_menu=parent_menu, sort_order=idx)
            if created:
                created_count += 1
            menu_map[node_name] = node_menu

            item_counter = 1
            if isinstance(children, dict):
                leaf_items = children.get("_items", [])
                for item_name in leaf_items:
                    leaf_menu, leaf_created = self._upsert_bound_menu(
                        menu_name=item_name,
                        parent_menu=node_menu,
                        form_map=form_map,
                        sort_order=item_counter,
                    )
                    if leaf_created:
                        created_count += 1
                    menu_map[item_name] = leaf_menu
                    item_counter += 1

                for child_name, child_value in children.items():
                    if child_name == "_items":
                        continue
                    child_menu, child_created = self._upsert_folder_menu(
                        name=child_name,
                        parent_menu=node_menu,
                        sort_order=item_counter,
                    )
                    if child_created:
                        created_count += 1
                    menu_map[child_name] = child_menu
                    item_counter += 1

                    if isinstance(child_value, list):
                        for sub_index, sub_item in enumerate(child_value, start=1):
                            leaf_menu, leaf_created = self._upsert_bound_menu(
                                menu_name=sub_item,
                                parent_menu=child_menu,
                                form_map=form_map,
                                sort_order=sub_index,
                            )
                            if leaf_created:
                                created_count += 1
                            menu_map[sub_item] = leaf_menu
            elif isinstance(children, list):
                for sub_index, sub_item in enumerate(children, start=1):
                    leaf_menu, leaf_created = self._upsert_bound_menu(
                        menu_name=sub_item,
                        parent_menu=node_menu,
                        form_map=form_map,
                        sort_order=sub_index,
                    )
                    if leaf_created:
                        created_count += 1
                    menu_map[sub_item] = leaf_menu
        return created_count

    @staticmethod
    def _upsert_folder_menu(*, name: str, parent_menu: Menu | None, sort_order: int) -> tuple[Menu, bool]:
        existing = Menu.objects.filter(name=name, parent_menu=parent_menu, form__isnull=True).order_by("id").first()
        if existing:
            changed = (
                existing.sort_order != sort_order
                or existing.is_system is not True
                or existing.form_id is not None
            )
            if changed:
                existing.sort_order = sort_order
                existing.is_system = True
                existing.form = None
                existing.save(update_fields=["sort_order", "is_system", "form"])
            return existing, False
        menu = Menu.objects.create(
            name=name,
            parent_menu=parent_menu,
            form=None,
            sort_order=sort_order,
            is_system=True,
        )
        return menu, True

    @staticmethod
    def _upsert_bound_menu(
        *, menu_name: str, parent_menu: Menu, form_map: dict[str, Form], sort_order: int
    ) -> tuple[Menu, bool]:
        if menu_name not in MENU_TO_FORM_TABLE:
            existing = Menu.objects.filter(name=menu_name, parent_menu=parent_menu, form__isnull=False).first()
            if existing:
                changed = (
                    existing.sort_order != sort_order
                    or existing.parent_menu_id != parent_menu.id
                    or existing.is_system is not True
                )
                if changed:
                    existing.sort_order = sort_order
                    existing.parent_menu = parent_menu
                    existing.is_system = True
                    existing.save(update_fields=["sort_order", "parent_menu", "is_system"])
                return existing, False
            raise CommandError(f"Menu '{menu_name}' cannot be bound because it has no mapped form.")

        table_name = MENU_TO_FORM_TABLE[menu_name]
        form = form_map.get(table_name)
        if not form:
            raise CommandError(f"Form table '{table_name}' is not initialized for menu '{menu_name}'.")

        menu = Menu.objects.filter(form=form).order_by("id").first()
        if menu:
            changed = (
                menu.name != menu_name
                or menu.parent_menu_id != parent_menu.id
                or menu.sort_order != sort_order
                or menu.is_system is not True
            )
            if changed:
                menu.name = menu_name
                menu.parent_menu = parent_menu
                menu.sort_order = sort_order
                menu.is_system = True
                menu.save(update_fields=["name", "parent_menu", "sort_order", "is_system"])
            return menu, False

        menu = Menu.objects.create(
            name=menu_name,
            parent_menu=parent_menu,
            form=form,
            sort_order=sort_order,
            is_system=True,
        )
        return menu, True

    def _ensure_permissions_and_security(self, menu_map: dict[str, Menu], summary: dict[str, dict[str, int]]) -> None:
        self.stdout.write("Ensuring permissions for root and demo groups ...")
        root_group_name = settings.HRMS["ROOT_GROUP_NAME"]
        root_group, _ = UserGroup.objects.get_or_create(
            name=root_group_name,
            defaults={"description": "Protected root administrator group"},
        )

        created_permissions = 0
        all_menus = list(Menu.objects.all())
        for menu in all_menus:
            _, created = Permission.objects.update_or_create(
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
            if created:
                created_permissions += 1

        hr_managers = UserGroup.objects.filter(name="HR Managers").first()
        hr_experts = UserGroup.objects.filter(name="HR Experts").first()
        auditors = UserGroup.objects.filter(name="Auditors").first()

        demo_groups = [group for group in [hr_managers, hr_experts, auditors] if group]
        for group in demo_groups:
            for menu_name in MENU_TO_FORM_TABLE:
                menu = menu_map.get(menu_name)
                if not menu:
                    continue
                defaults = {
                    "can_view": True,
                    "can_insert": True,
                    "can_update": True,
                    "can_delete": group.name != "Auditors",
                    "can_print": True,
                }
                if group.name == "Auditors":
                    defaults["can_insert"] = False
                    defaults["can_update"] = False
                if group.name == "HR Experts":
                    defaults["can_delete"] = False

                _, created = Permission.objects.update_or_create(menu=menu, group=group, defaults=defaults)
                if created:
                    created_permissions += 1

        root_username = settings.HRMS["ROOT_USERNAME"]
        user_model = get_user_model()
        root_user, created = user_model.objects.get_or_create(
            username=root_username,
            defaults={"is_superuser": True, "is_staff": True, "is_active": True},
        )
        if created:
            root_user.set_password(settings.HRMS["ROOT_PASSWORD"])
            root_user.save(update_fields=["password"])
        root_user.groups_ref.add(root_group)

        summary["permissions"]["permissions_created"] = created_permissions
        summary["permissions"]["permissions_total"] = Permission.objects.count()
        summary["permissions"]["root_group"] = root_group.id
        summary["permissions"]["root_user"] = root_user.id

    def _ensure_demo_groups_and_users(self, summary: dict[str, dict[str, int]]) -> None:
        self.stdout.write("Ensuring demo groups and memberships ...")
        created_groups = 0
        for group_name, description in GROUP_DEFINITIONS:
            _, created = UserGroup.objects.get_or_create(
                name=group_name,
                defaults={"description": description},
            )
            if created:
                created_groups += 1

        user_model = get_user_model()
        demo_users = [
            ("hr_manager", "HR Managers", True),
            ("hr_expert", "HR Experts", False),
            ("auditor_user", "Auditors", False),
        ]
        created_users = 0
        for username, group_name, is_staff in demo_users:
            user, created = user_model.objects.get_or_create(
                username=username,
                defaults={"is_superuser": False, "is_staff": is_staff, "is_active": True},
            )
            if created:
                user.set_password("ChangeMe123!")
                user.save(update_fields=["password"])
                created_users += 1
            group = UserGroup.objects.filter(name=group_name).first()
            if group:
                user.groups_ref.add(group)

        summary["permissions"]["groups_created"] = created_groups
        summary["permissions"]["users_created"] = created_users

    def _reset_dynamic_demo_data(self) -> None:
        self.stdout.write(self.style.WARNING("Resetting demo dynamic data rows ..."))
        engine = get_engine()
        metadata = MetaData()
        with engine.begin() as connection:
            for table_name in [
                "dependent",
                "contract",
                "hokm",
                "internal_experience",
                "external_experience",
                "employee",
                "organization_unit",
            ]:
                if inspect(engine).has_table(table_name):
                    table = Table(table_name, metadata, autoload_with=engine)
                    connection.execute(delete(table))

    def _seed_business_data(
        self,
        form_map: dict[str, Form],
        lookup_map: dict[str, dict[str, int]],
        rng: random.Random,
        summary: dict[str, dict[str, int]],
    ) -> None:
        self.stdout.write("Seeding organization units and HR records ...")
        now = timezone.now().isoformat()
        engine = get_engine()
        metadata = MetaData()
        tables = {}
        for table_name in [
            "organization_unit",
            "employee",
            "dependent",
            "contract",
            "hokm",
            "internal_experience",
            "external_experience",
        ]:
            form = form_map.get(table_name)
            if form is None:
                raise CommandError(f"Missing form for table '{table_name}'.")
            if not inspect(engine).has_table(table_name):
                raise CommandError(f"Physical table '{table_name}' does not exist.")
            tables[table_name] = Table(table_name, metadata, autoload_with=engine)

        with engine.begin() as connection:
            # Idempotency: skip generation when employees already exist unless reset flag was used.
            employee_count = connection.execute(select(func.count()).select_from(tables["employee"])).scalar_one()
            if employee_count > 0:
                self.stdout.write(
                    self.style.WARNING(
                        "Employee rows already exist in demo tables. Skipping business data generation."
                    )
                )
                summary["records"]["organization_unit"] = connection.execute(
                    select(func.count()).select_from(tables["organization_unit"])
                ).scalar_one()
                summary["records"]["employee"] = employee_count
                summary["records"]["dependent"] = connection.execute(
                    select(func.count()).select_from(tables["dependent"])
                ).scalar_one()
                summary["records"]["contract"] = connection.execute(
                    select(func.count()).select_from(tables["contract"])
                ).scalar_one()
                summary["records"]["hokm"] = connection.execute(
                    select(func.count()).select_from(tables["hokm"])
                ).scalar_one()
                summary["records"]["internal_experience"] = connection.execute(
                    select(func.count()).select_from(tables["internal_experience"])
                ).scalar_one()
                summary["records"]["external_experience"] = connection.execute(
                    select(func.count()).select_from(tables["external_experience"])
                ).scalar_one()
                return

            unit_ids = self._insert_organization_units(connection, tables["organization_unit"], now)
            employee_rows = self._build_employees(rng=rng, unit_ids=unit_ids, city_lookup=lookup_map["City"], now=now)
            employee_result = connection.execute(
                tables["employee"].insert().returning(tables["employee"].c.id),
                employee_rows,
            )
            employee_ids = [int(row[0]) for row in employee_result]

            dependent_rows = []
            contract_rows = []
            hokm_rows = []
            internal_rows = []
            external_rows = []

            for employee_id in employee_ids:
                dependent_rows.extend(
                    self._build_dependents_for_employee(
                        employee_id=employee_id,
                        rng=rng,
                        relation_lookup=lookup_map["Relation"],
                        now=now,
                    )
                )
                contract_rows.extend(
                    self._build_contracts_for_employee(
                        employee_id=employee_id,
                        rng=rng,
                        contract_lookup=lookup_map["Contract"],
                        now=now,
                    )
                )
                hokm_rows.extend(self._build_hokm_for_employee(employee_id=employee_id, rng=rng, now=now))
                internal_rows.extend(
                    self._build_internal_experiences_for_employee(
                        employee_id=employee_id,
                        rng=rng,
                        city_lookup=lookup_map["City"],
                        education_lookup=lookup_map["Education"],
                        contract_lookup=lookup_map["Contract"],
                        status_lookup=lookup_map["EmploymentStatus"],
                        now=now,
                    )
                )
                external_rows.extend(
                    self._build_external_experiences_for_employee(
                        employee_id=employee_id,
                        rng=rng,
                        education_lookup=lookup_map["Education"],
                        contract_lookup=lookup_map["Contract"],
                        now=now,
                    )
                )

            if dependent_rows:
                connection.execute(tables["dependent"].insert(), dependent_rows)
            if contract_rows:
                connection.execute(tables["contract"].insert(), contract_rows)
            if hokm_rows:
                connection.execute(tables["hokm"].insert(), hokm_rows)
            if internal_rows:
                connection.execute(tables["internal_experience"].insert(), internal_rows)
            if external_rows:
                connection.execute(tables["external_experience"].insert(), external_rows)

            summary["records"]["organization_unit"] = len(unit_ids)
            summary["records"]["employee"] = len(employee_rows)
            summary["records"]["dependent"] = len(dependent_rows)
            summary["records"]["contract"] = len(contract_rows)
            summary["records"]["hokm"] = len(hokm_rows)
            summary["records"]["internal_experience"] = len(internal_rows)
            summary["records"]["external_experience"] = len(external_rows)

    @staticmethod
    def _insert_organization_units(connection, org_table: Table, now: str) -> list[int]:
        org_rows = [
            {"name": "Central Headquarters", "description": "Main head office", "parent_organization_id": None, "created_at": now, "updated_at": now},
            {"name": "Human Resources Department", "description": "Recruitment and employee affairs", "parent_organization_id": 1, "created_at": now, "updated_at": now},
            {"name": "Information Technology Department", "description": "Infrastructure and applications", "parent_organization_id": 1, "created_at": now, "updated_at": now},
            {"name": "Finance Department", "description": "Accounting and payroll", "parent_organization_id": 1, "created_at": now, "updated_at": now},
        ]
        inserted_root = connection.execute(
            org_table.insert().returning(org_table.c.id),
            [org_rows[0]],
        ).first()
        root_id = int(inserted_root[0])
        child_rows = [
            {**org_rows[1], "parent_organization_id": root_id},
            {**org_rows[2], "parent_organization_id": root_id},
            {**org_rows[3], "parent_organization_id": root_id},
        ]
        child_ids = connection.execute(org_table.insert().returning(org_table.c.id), child_rows).fetchall()
        return [root_id] + [int(row[0]) for row in child_ids]

    def _build_employees(
        self,
        *,
        rng: random.Random,
        unit_ids: list[int],
        city_lookup: dict[str, int],
        now: str,
    ) -> list[dict]:
        first_names = [
            "Ali", "Reza", "Hossein", "Mehdi", "Saeed", "Amir", "Mohammad", "Arman", "Nima", "Pouya",
            "Sara", "Neda", "Fatemeh", "Maryam", "Leila", "Parisa", "Shiva", "Mina", "Roya", "Arezoo",
            "Yasaman", "Mahsa", "Hamed", "Navid", "Ehsan", "Soheil", "Milad", "Sina", "Kaveh", "Farhad",
        ]
        last_names = [
            "Ahmadi", "Mohammadi", "Hosseini", "Karimi", "Rahimi", "Moradi", "Jafari", "Kazemi", "Ghasemi", "Yousefi",
            "Rostami", "Soleimani", "Ebrahimi", "Shirazi", "Najafi", "Tavakoli", "Amini", "Naseri", "Sadeghi", "Hosseinzadeh",
            "Sharifi", "Azizi", "Farhadi", "Jalali", "Mahdavi", "Zare", "Nikbakht", "Bakhtiari", "Khodadadi", "Davoodi",
        ]
        father_names = [
            "Hasan", "Akbar", "Mahmoud", "Javad", "Abbas", "Majid", "Morteza", "Parviz", "Bahram", "Jalal",
            "Ahmad", "Taghi", "Davood", "Hamid", "Masoud", "Fariborz", "Farrokh", "Kamran", "Naser", "Jahan",
        ]
        cities = list(city_lookup.keys())
        rows: list[dict] = []

        for index in range(1, 51):
            first_name = rng.choice(first_names)
            last_name = rng.choice(last_names)
            father_name = rng.choice(father_names)
            birth_year = rng.randint(1360, 1381)
            birth_month = rng.randint(1, 12)
            birth_day = rng.randint(1, 28)
            # Gregorian-like year range for ISO date format expected by backend
            gregorian_year = birth_year + 621
            birth_date = date(gregorian_year, birth_month, birth_day)

            national_code = f"14{index:08d}"
            rows.append(
                {
                    "first_name": first_name,
                    "last_name": last_name,
                    "father_name": father_name,
                    "national_code": national_code,
                    "birth_date": birth_date.isoformat(),
                    "birth_city": city_lookup[rng.choice(cities)],
                    "organization_id": unit_ids[index % len(unit_ids)],
                    "created_at": now,
                    "updated_at": now,
                }
            )
        return rows

    def _build_dependents_for_employee(
        self,
        *,
        employee_id: int,
        rng: random.Random,
        relation_lookup: dict[str, int],
        now: str,
    ) -> list[dict]:
        count = rng.randint(0, 4)
        first_names = ["Mahin", "Sahar", "Amirhossein", "Negin", "Peyman", "Saba", "Yas", "Shahin", "Bahar", "Kian"]
        last_names = ["Ahmadi", "Karimi", "Rahimi", "Moradi", "Jafari", "Tavakoli", "Azizi", "Zarei", "Hosseini", "Shirazi"]
        rows = []
        for idx in range(1, count + 1):
            relation_key = "Spouse" if idx == 1 and rng.random() > 0.5 else "Child"
            rows.append(
                {
                    "employee_id": employee_id,
                    "first_name": rng.choice(first_names),
                    "last_name": rng.choice(last_names),
                    "national_code": f"24{employee_id:04d}{idx:04d}",
                    "relation_type": relation_lookup[relation_key],
                    "created_at": now,
                    "updated_at": now,
                }
            )
        return rows

    def _build_contracts_for_employee(
        self,
        *,
        employee_id: int,
        rng: random.Random,
        contract_lookup: dict[str, int],
        now: str,
    ) -> list[dict]:
        count = rng.randint(3, 6)
        contract_values = list(contract_lookup.values())
        base_start = date(2014, rng.randint(1, 12), rng.randint(1, 28))
        rows = []
        current_start = base_start
        for idx in range(1, count + 1):
            period_days = rng.randint(240, 540)
            to_date = current_start + timedelta(days=period_days)
            issue_date = current_start - timedelta(days=rng.randint(7, 60))
            registration_date = issue_date + timedelta(days=rng.randint(0, 15))
            rows.append(
                {
                    "employee_id": employee_id,
                    "from_date": current_start.isoformat(),
                    "to_date": to_date.isoformat() if idx < count else None,
                    "contract_type": rng.choice(contract_values),
                    "secretariat_number": f"CTR-{employee_id:04d}-{idx:02d}",
                    "issue_date": issue_date.isoformat(),
                    "registration_date": registration_date.isoformat(),
                    "created_at": now,
                    "updated_at": now,
                }
            )
            current_start = to_date + timedelta(days=rng.randint(1, 45))
        return rows

    def _build_hokm_for_employee(self, *, employee_id: int, rng: random.Random, now: str) -> list[dict]:
        count = rng.randint(3, 6)
        start_date = date(2015, rng.randint(1, 12), rng.randint(1, 28))
        rows = []
        for _ in range(count):
            calculation_date = start_date + timedelta(days=rng.randint(120, 420))
            execution_date = calculation_date + timedelta(days=rng.randint(0, 30))
            rows.append(
                {
                    "employee_id": employee_id,
                    "calculation_date": calculation_date.isoformat(),
                    "execution_date": execution_date.isoformat(),
                    "created_at": now,
                    "updated_at": now,
                }
            )
            start_date = execution_date
        return rows

    def _build_internal_experiences_for_employee(
        self,
        *,
        employee_id: int,
        rng: random.Random,
        city_lookup: dict[str, int],
        education_lookup: dict[str, int],
        contract_lookup: dict[str, int],
        status_lookup: dict[str, int],
        now: str,
    ) -> list[dict]:
        count = rng.randint(3, 6)
        start = date(2013, rng.randint(1, 12), rng.randint(1, 28))
        rows = []
        job_titles = ["HR Expert", "Senior HR Expert", "Analyst", "Coordinator", "Supervisor", "Specialist"]
        fields = ["Management", "Computer Engineering", "Accounting", "Industrial Engineering", "Law", "Economics"]
        education_values = list(education_lookup.values())
        contract_values = list(contract_lookup.values())
        status_values = list(status_lookup.values())
        city_values = list(city_lookup.values())
        for idx in range(count):
            duration = rng.randint(240, 700)
            end = start + timedelta(days=duration)
            rows.append(
                {
                    "employee_id": employee_id,
                    "from_date": start.isoformat(),
                    "to_date": None if idx == count - 1 and rng.random() > 0.45 else end.isoformat(),
                    "education_degree": rng.choice(education_values),
                    "field_of_study": rng.choice(fields),
                    "employment_type": rng.choice(contract_values),
                    "job_title": rng.choice(job_titles),
                    "work_city": rng.choice(city_values),
                    "employment_status": rng.choice(status_values),
                    "created_at": now,
                    "updated_at": now,
                }
            )
            start = end + timedelta(days=rng.randint(10, 80))
        return rows

    def _build_external_experiences_for_employee(
        self,
        *,
        employee_id: int,
        rng: random.Random,
        education_lookup: dict[str, int],
        contract_lookup: dict[str, int],
        now: str,
    ) -> list[dict]:
        count = rng.randint(3, 6)
        start = date(2008, rng.randint(1, 12), rng.randint(1, 28))
        rows = []
        fields = ["Software", "Business", "Public Administration", "Accounting", "Project Management", "Statistics"]
        job_titles = ["Consultant", "Officer", "Engineer", "Assistant", "Administrator", "Coordinator"]
        education_values = list(education_lookup.values())
        contract_values = list(contract_lookup.values())
        for _ in range(count):
            duration = rng.randint(180, 600)
            end = start + timedelta(days=duration)
            rows.append(
                {
                    "employee_id": employee_id,
                    "from_date": start.isoformat(),
                    "to_date": end.isoformat(),
                    "education_degree": rng.choice(education_values),
                    "field_of_study": rng.choice(fields),
                    "employment_type": rng.choice(contract_values),
                    "job_title": rng.choice(job_titles),
                    "created_at": now,
                    "updated_at": now,
                }
            )
            start = end + timedelta(days=rng.randint(30, 120))
        return rows

    def _print_summary(self, summary: dict[str, dict[str, int]], seed: int) -> None:
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("===== Demo Seed Summary ====="))
        self.stdout.write(f"Seed: {seed}")
        self.stdout.write("")

        self.stdout.write("Menus:")
        self.stdout.write(f"  Created this run: {summary['menus'].get('menus_created', 0)}")
        self.stdout.write(f"  Total target in hierarchy: {summary['menus'].get('menus_total_target', 0)}")
        self.stdout.write("  Roots: System, Human Resources")
        self.stdout.write("")

        self.stdout.write("Forms:")
        self.stdout.write(f"  Created this run: {summary['forms'].get('forms_created', 0)}")
        self.stdout.write(f"  Total expected forms: {summary['forms'].get('forms_total', 0)}")
        self.stdout.write(f"  Form fields created this run: {summary['forms'].get('form_fields_created', 0)}")
        self.stdout.write(f"  Total expected form fields: {summary['forms'].get('form_fields_total', 0)}")
        self.stdout.write("")

        self.stdout.write("Lookups:")
        self.stdout.write(f"  Lookup types created this run: {summary['lookups'].get('lookup_types_created', 0)}")
        self.stdout.write(f"  Lookup values created this run: {summary['lookups'].get('lookup_values_created', 0)}")
        self.stdout.write(f"  Total lookup types expected: {summary['lookups'].get('lookup_types_total', 0)}")
        self.stdout.write(f"  Total lookup values expected: {summary['lookups'].get('lookup_values_total', 0)}")
        self.stdout.write("")

        self.stdout.write("Permissions and security:")
        self.stdout.write(f"  Permission rows created this run: {summary['permissions'].get('permissions_created', 0)}")
        self.stdout.write(f"  Permission rows total: {summary['permissions'].get('permissions_total', 0)}")
        self.stdout.write(f"  Groups created this run: {summary['permissions'].get('groups_created', 0)}")
        self.stdout.write(f"  Users created this run: {summary['permissions'].get('users_created', 0)}")
        self.stdout.write(f"  Root user id: {summary['permissions'].get('root_user', 'N/A')}")
        self.stdout.write(f"  Root group id: {summary['permissions'].get('root_group', 'N/A')}")
        self.stdout.write("")

        self.stdout.write("Generated records:")
        for table in [
            "organization_unit",
            "employee",
            "dependent",
            "contract",
            "hokm",
            "internal_experience",
            "external_experience",
        ]:
            self.stdout.write(f"  {table}: {summary['records'].get(table, 0)}")
        self.stdout.write("============================")
