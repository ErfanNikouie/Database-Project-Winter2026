from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from db.database import Base


# -------------------------
# Security / Users
# -------------------------


class User(Base):
    __tablename__ = "User"

    Id: Mapped[int] = mapped_column(Integer, primary_key=True)
    HasConfidentialAccess: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    PasswordHash: Mapped[str] = mapped_column(String(255), nullable=False)
    Username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    AccessLevel: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    IsActive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class UserGroup(Base):
    __tablename__ = "UserGroup"

    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    Name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    Description: Mapped[str | None] = mapped_column(String(255))


class UserUserGroup(Base):
    __tablename__ = "UserUserGroup"

    UserGroupId: Mapped[int] = mapped_column(ForeignKey("UserGroup.Id"), primary_key=True)
    UserId: Mapped[int] = mapped_column(ForeignKey("User.Id"), primary_key=True)


# -------------------------
# Meta: Menus / Forms
# -------------------------


class Form(Base):
    __tablename__ = "Form"
    __table_args__ = (
        UniqueConstraint("TableName", name="uq_form_table_name"),
        UniqueConstraint("Name", name="uq_form_name"),
    )

    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    Name: Mapped[str] = mapped_column(String(150), nullable=False)
    Description: Mapped[str | None] = mapped_column(Text)
    TableName: Mapped[str] = mapped_column(String(150), nullable=False)

    Fields: Mapped[list[FormField]] = relationship("FormField", back_populates="Form", cascade="all, delete-orphan")


class FormField(Base):
    __tablename__ = "FormField"
    __table_args__ = (
        UniqueConstraint("FormId", "FieldName", name="uq_form_field_unique"),
    )

    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    FormId: Mapped[int] = mapped_column(ForeignKey("Form.Id"), nullable=False, index=True)

    FieldName: Mapped[str] = mapped_column(String(150), nullable=False)
    FieldType: Mapped[str] = mapped_column(String(50), nullable=False)  # text, number, date, lookup, ...
    Mandatory: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    LookupId: Mapped[int | None] = mapped_column(ForeignKey("Lookup.Id"), nullable=True)
    # For FieldType == 'foreign_key': name of the target table this field points to.
    # (We store table name instead of a formal FK constraint to support fully dynamic schemas.)
    TargetTableName: Mapped[str | None] = mapped_column(String(150), nullable=True)

    Form: Mapped[Form] = relationship("Form", back_populates="Fields")
    Lookup: Mapped[Lookup | None] = relationship("Lookup")


class Menu(Base):
    __tablename__ = "Menu"

    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    Name: Mapped[str] = mapped_column(String(150), nullable=False)

    ParentId: Mapped[int | None] = mapped_column(ForeignKey("Menu.Id"), nullable=True, index=True)
    FormId: Mapped[int | None] = mapped_column(ForeignKey("Form.Id"), nullable=True)

    Parent: Mapped[Menu | None] = relationship("Menu", remote_side=[Id], back_populates="Children")
    Children: Mapped[list[Menu]] = relationship("Menu", back_populates="Parent", cascade="all")

    Form: Mapped[Form | None] = relationship("Form")


class Permission(Base):
    __tablename__ = "Permission"

    UserGroupId: Mapped[int] = mapped_column(ForeignKey("UserGroup.Id"), primary_key=True)
    MenuId: Mapped[int] = mapped_column(ForeignKey("Menu.Id"), primary_key=True)

    CanView: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    CanInsert: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    CanEdit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    CanDelete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    CanPrint: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


# -------------------------
# Lookups
# -------------------------


class Lookup(Base):
    __tablename__ = "Lookup"

    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    Name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    Description: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)

    Values: Mapped[list[LookupValues]] = relationship(
        "LookupValues", back_populates="Lookup", cascade="all, delete-orphan"
    )


class LookupValues(Base):
    __tablename__ = "LookupValues"
    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    LookupId: Mapped[int] = mapped_column(ForeignKey("Lookup.Id"), nullable=False, index=True)
    Value: Mapped[str] = mapped_column(String(200), nullable=False)

    Lookup: Mapped[Lookup] = relationship("Lookup", back_populates="Values")


# -------------------------
# HR "core" physical tables
# (These exist so the prototype always has the required tables,
# even before the user creates dynamic Form metadata.)
# -------------------------


class OrganizationUnit(Base):
    __tablename__ = "OrganizationUnit"

    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    Name: Mapped[str] = mapped_column(String(150), nullable=False)
    Description: Mapped[str | None] = mapped_column(String(255))
    ParentId: Mapped[int | None] = mapped_column(ForeignKey("OrganizationUnit.Id"), nullable=True)


class Employee(Base):
    __tablename__ = "Employee"

    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    FirstName: Mapped[str] = mapped_column(String(100), nullable=False)
    LastName: Mapped[str] = mapped_column(String(100), nullable=False)
    FatherName: Mapped[str | None] = mapped_column(String(100))
    NationalCode: Mapped[str | None] = mapped_column(String(30))
    BirthDate: Mapped[str | None] = mapped_column(String(30))  # ISO string
    BirthCity: Mapped[str | None] = mapped_column(String(100))
    OrganizationUnitId: Mapped[int | None] = mapped_column(ForeignKey("OrganizationUnit.Id"), nullable=True)


class Dependent(Base):
    __tablename__ = "Dependent"

    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    EmployeeId: Mapped[int] = mapped_column(ForeignKey("Employee.Id"), nullable=False, index=True)
    FirstName: Mapped[str] = mapped_column(String(100), nullable=False)
    LastName: Mapped[str] = mapped_column(String(100), nullable=False)
    NationalCode: Mapped[str | None] = mapped_column(String(30))
    RelationType: Mapped[str | None] = mapped_column(String(50))


class Contract(Base):
    __tablename__ = "Contract"

    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    EmployeeId: Mapped[int] = mapped_column(ForeignKey("Employee.Id"), nullable=False, index=True)
    FromDate: Mapped[str | None] = mapped_column(String(30))
    ToDate: Mapped[str | None] = mapped_column(String(30))
    ContractType: Mapped[str | None] = mapped_column(String(50))
    RegistrationDate: Mapped[str | None] = mapped_column(String(30))
    SecretariatNumber: Mapped[str | None] = mapped_column(String(50))
    IssueDate: Mapped[str | None] = mapped_column(String(30))


class Hokm(Base):
    __tablename__ = "Hokm"

    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    EmployeeId: Mapped[int] = mapped_column(ForeignKey("Employee.Id"), nullable=False, index=True)
    CalculationDate: Mapped[str | None] = mapped_column(String(30))
    ExecutionDate: Mapped[str | None] = mapped_column(String(30))


class ExternalExperience(Base):
    __tablename__ = "ExternalExperience"

    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    EmployeeId: Mapped[int] = mapped_column(ForeignKey("Employee.Id"), nullable=False, index=True)
    FromDate: Mapped[str | None] = mapped_column(String(30))
    ToDate: Mapped[str | None] = mapped_column(String(30))
    EducationDegree: Mapped[str | None] = mapped_column(String(50))
    FieldOfStudy: Mapped[str | None] = mapped_column(String(100))
    EmploymentType: Mapped[str | None] = mapped_column(String(50))
    JobTitle: Mapped[str | None] = mapped_column(String(100))
    Duration: Mapped[str | None] = mapped_column(String(50))


class InternalExperience(Base):
    __tablename__ = "InternalExperience"

    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    EmployeeId: Mapped[int] = mapped_column(ForeignKey("Employee.Id"), nullable=False, index=True)
    FromDate: Mapped[str | None] = mapped_column(String(30))
    ToDate: Mapped[str | None] = mapped_column(String(30))
    EducationDegree: Mapped[str | None] = mapped_column(String(50))
    FieldOfStudy: Mapped[str | None] = mapped_column(String(100))
    EmploymentType: Mapped[str | None] = mapped_column(String(50))
    JobTitle: Mapped[str | None] = mapped_column(String(100))
    Duration: Mapped[str | None] = mapped_column(String(50))
    OrganizationUnitId: Mapped[int | None] = mapped_column(ForeignKey("OrganizationUnit.Id"), nullable=True)
    WorkCity: Mapped[str | None] = mapped_column(String(100))
    EmploymentStatus: Mapped[str | None] = mapped_column(String(50))


