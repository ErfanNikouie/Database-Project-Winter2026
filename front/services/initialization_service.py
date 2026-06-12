from __future__ import annotations

from sqlalchemy import select

from db.database import session_scope
from db.models import Form, FormField, Menu
from services.dynamic_table_service import DynamicTableService
from utils.naming import safe_identifier


HR_ROOT_MENU_NAME = "HR"


def _ensure_form(session, *, name: str, description: str, table_name: str) -> Form:
    existing = session.execute(select(Form).where(Form.TableName == table_name)).scalar_one_or_none()
    if existing:
        return existing
    f = Form(Name=name, Description=description, TableName=table_name)
    session.add(f)
    session.flush()
    return f


def _ensure_field(
    session,
    *,
    form_id: int,
    field_name: str,
    field_type: str,
    mandatory: bool = False,
    lookup_id: int | None = None,
    target_table_name: str | None = None,
) -> None:
    safe_identifier(field_name, label="field name")
    exists = session.execute(
        select(FormField).where(FormField.FormId == form_id, FormField.FieldName == field_name)
    ).scalar_one_or_none()
    if exists:
        # Converge to desired definition (idempotent + upgrade-friendly)
        exists.FieldType = field_type
        exists.Mandatory = bool(mandatory)
        exists.LookupId = lookup_id
        exists.TargetTableName = (target_table_name.strip() if target_table_name else None)
        return
    session.add(
        FormField(
            FormId=form_id,
            FieldName=field_name,
            FieldType=field_type,
            Mandatory=bool(mandatory),
            LookupId=lookup_id,
            TargetTableName=(target_table_name.strip() if target_table_name else None),
        )
    )


def _ensure_menu(session, *, name: str, parent_id: int | None, form_id: int | None) -> Menu:
    existing = session.execute(
        select(Menu).where(Menu.ParentId == parent_id, Menu.Name == name)
    ).scalar_one_or_none()
    if existing:
        # Update in case form got set later
        existing.FormId = form_id
        return existing
    m = Menu(Name=name, ParentId=parent_id, FormId=form_id)
    session.add(m)
    session.flush()
    return m


def initialize_default_hr_configuration() -> None:
    """Create default HR forms + menu entries (idempotent).

    Physical tables already exist from ORM models, but we still "sync" them to guarantee
    a consistent schema for the dynamic engine.
    """

    with session_scope() as session:
        hr_root = _ensure_menu(session, name=HR_ROOT_MENU_NAME, parent_id=None, form_id=None)

        # Forms
        org_form = _ensure_form(
            session,
            name="Organization Units",
            description="Organization unit hierarchy",
            table_name="OrganizationUnit",
        )
        emp_form = _ensure_form(session, name="Employees", description="Employees", table_name="Employee")
        dep_form = _ensure_form(session, name="Dependents", description="Employee dependents", table_name="Dependent")
        contract_form = _ensure_form(session, name="Contracts", description="Employee contracts", table_name="Contract")
        hokm_form = _ensure_form(session, name="Hokm", description="Hokm records", table_name="Hokm")
        ext_exp_form = _ensure_form(
            session,
            name="External Experiences",
            description="External experience",
            table_name="ExternalExperience",
        )
        int_exp_form = _ensure_form(
            session,
            name="Internal Experiences",
            description="Internal experience",
            table_name="InternalExperience",
        )

        # Fields - OrganizationUnit
        _ensure_field(session, form_id=org_form.Id, field_name="Name", field_type="text", mandatory=True)
        _ensure_field(session, form_id=org_form.Id, field_name="Description", field_type="text")
        _ensure_field(session, form_id=org_form.Id, field_name="ParentId", field_type="integer")

        # Fields - Employee
        _ensure_field(session, form_id=emp_form.Id, field_name="FirstName", field_type="text", mandatory=True)
        _ensure_field(session, form_id=emp_form.Id, field_name="LastName", field_type="text", mandatory=True)
        _ensure_field(session, form_id=emp_form.Id, field_name="FatherName", field_type="text")
        _ensure_field(session, form_id=emp_form.Id, field_name="NationalCode", field_type="text")
        _ensure_field(session, form_id=emp_form.Id, field_name="BirthDate", field_type="date")
        _ensure_field(session, form_id=emp_form.Id, field_name="BirthCity", field_type="text")
        _ensure_field(
            session,
            form_id=emp_form.Id,
            field_name="OrganizationUnitId",
            field_type="foreign_key",
            target_table_name="OrganizationUnit",
        )

        # Fields - Dependent
        _ensure_field(
            session,
            form_id=dep_form.Id,
            field_name="EmployeeId",
            field_type="foreign_key",
            mandatory=True,
            target_table_name="Employee",
        )
        _ensure_field(session, form_id=dep_form.Id, field_name="FirstName", field_type="text", mandatory=True)
        _ensure_field(session, form_id=dep_form.Id, field_name="LastName", field_type="text", mandatory=True)
        _ensure_field(session, form_id=dep_form.Id, field_name="NationalCode", field_type="text")
        _ensure_field(session, form_id=dep_form.Id, field_name="RelationType", field_type="text")

        # Fields - Contract
        _ensure_field(
            session,
            form_id=contract_form.Id,
            field_name="EmployeeId",
            field_type="foreign_key",
            mandatory=True,
            target_table_name="Employee",
        )
        _ensure_field(session, form_id=contract_form.Id, field_name="FromDate", field_type="date")
        _ensure_field(session, form_id=contract_form.Id, field_name="ToDate", field_type="date")
        _ensure_field(session, form_id=contract_form.Id, field_name="ContractType", field_type="text")
        _ensure_field(session, form_id=contract_form.Id, field_name="RegistrationDate", field_type="date")
        _ensure_field(session, form_id=contract_form.Id, field_name="SecretariatNumber", field_type="text")
        _ensure_field(session, form_id=contract_form.Id, field_name="IssueDate", field_type="date")

        # Fields - Hokm
        _ensure_field(
            session,
            form_id=hokm_form.Id,
            field_name="EmployeeId",
            field_type="foreign_key",
            mandatory=True,
            target_table_name="Employee",
        )
        _ensure_field(session, form_id=hokm_form.Id, field_name="CalculationDate", field_type="date")
        _ensure_field(session, form_id=hokm_form.Id, field_name="ExecutionDate", field_type="date")

        # Fields - ExternalExperience
        _ensure_field(
            session,
            form_id=ext_exp_form.Id,
            field_name="EmployeeId",
            field_type="foreign_key",
            mandatory=True,
            target_table_name="Employee",
        )
        _ensure_field(session, form_id=ext_exp_form.Id, field_name="FromDate", field_type="date")
        _ensure_field(session, form_id=ext_exp_form.Id, field_name="ToDate", field_type="date")
        _ensure_field(session, form_id=ext_exp_form.Id, field_name="EducationDegree", field_type="text")
        _ensure_field(session, form_id=ext_exp_form.Id, field_name="FieldOfStudy", field_type="text")
        _ensure_field(session, form_id=ext_exp_form.Id, field_name="EmploymentType", field_type="text")
        _ensure_field(session, form_id=ext_exp_form.Id, field_name="JobTitle", field_type="text")
        _ensure_field(session, form_id=ext_exp_form.Id, field_name="Duration", field_type="text")

        # Fields - InternalExperience
        _ensure_field(
            session,
            form_id=int_exp_form.Id,
            field_name="EmployeeId",
            field_type="foreign_key",
            mandatory=True,
            target_table_name="Employee",
        )
        _ensure_field(session, form_id=int_exp_form.Id, field_name="FromDate", field_type="date")
        _ensure_field(session, form_id=int_exp_form.Id, field_name="ToDate", field_type="date")
        _ensure_field(session, form_id=int_exp_form.Id, field_name="EducationDegree", field_type="text")
        _ensure_field(session, form_id=int_exp_form.Id, field_name="FieldOfStudy", field_type="text")
        _ensure_field(session, form_id=int_exp_form.Id, field_name="EmploymentType", field_type="text")
        _ensure_field(session, form_id=int_exp_form.Id, field_name="JobTitle", field_type="text")
        _ensure_field(session, form_id=int_exp_form.Id, field_name="Duration", field_type="text")
        _ensure_field(
            session,
            form_id=int_exp_form.Id,
            field_name="OrganizationUnitId",
            field_type="foreign_key",
            target_table_name="OrganizationUnit",
        )
        _ensure_field(session, form_id=int_exp_form.Id, field_name="WorkCity", field_type="text")
        _ensure_field(session, form_id=int_exp_form.Id, field_name="EmploymentStatus", field_type="text")

        # HR Menus
        _ensure_menu(session, name="Organization Units", parent_id=hr_root.Id, form_id=org_form.Id)
        _ensure_menu(session, name="Employees", parent_id=hr_root.Id, form_id=emp_form.Id)
        _ensure_menu(session, name="Dependents", parent_id=hr_root.Id, form_id=dep_form.Id)
        _ensure_menu(session, name="Contracts", parent_id=hr_root.Id, form_id=contract_form.Id)
        _ensure_menu(session, name="Hokm", parent_id=hr_root.Id, form_id=hokm_form.Id)
        _ensure_menu(session, name="External Experiences", parent_id=hr_root.Id, form_id=ext_exp_form.Id)
        _ensure_menu(session, name="Internal Experiences", parent_id=hr_root.Id, form_id=int_exp_form.Id)

        # Materialize fields now (table sync). We need the latest fields so query again.
        forms = [org_form, emp_form, dep_form, contract_form, hokm_form, ext_exp_form, int_exp_form]
        session.flush()

    # Sync after session commit (ensures forms/fields committed)
    dts = DynamicTableService()
    with session_scope() as session:
        for f in session.execute(select(Form).where(Form.TableName.in_([
            "OrganizationUnit",
            "Employee",
            "Dependent",
            "Contract",
            "Hokm",
            "ExternalExperience",
            "InternalExperience",
        ]))).scalars().all():
            fields = session.execute(select(FormField).where(FormField.FormId == f.Id)).scalars().all()
            dts.ensure_table(f, fields)

