from __future__ import annotations

from sqlalchemy import select, inspect, text

from db.database import Base, get_engine, session_scope
from db import models


SYSTEM_ROOT_MENU_NAME = "System"


def create_all_tables() -> None:
    """Create ALL known ORM tables.

    This includes:
    - Meta tables (forms, fields, menus, lookups, permissions, users)
    - Required HR physical tables (Employee, Contract, ...)

    Dynamic user-defined form tables are handled separately by DynamicTableService.
    """
    engine = get_engine()
    Base.metadata.create_all(engine)


def ensure_admin_and_system_seed() -> None:
    """Ensure the minimal required seed data exists."""
    with session_scope() as session:
        # Admin user
        admin = session.get(models.User, 0)
        if admin is None:
            session.add(
                models.User(
                    Id=0,
                    Username="admin",
                    PasswordHash="admin",  # prototype; structure supports hashing later
                    HasConfidentialAccess=True,
                    AccessLevel=999,
                    IsActive=True,
                )
            )

        # Root menu
        root_menu = session.execute(
            select(models.Menu).where(models.Menu.ParentId.is_(None), models.Menu.Name == SYSTEM_ROOT_MENU_NAME)
        ).scalar_one_or_none()
        if root_menu is None:
            root_menu = models.Menu(Name=SYSTEM_ROOT_MENU_NAME, ParentId=None, FormId=None)
            session.add(root_menu)
            session.flush()  # get Id

        root_menu_id = int(root_menu.Id)  # type: ignore[arg-type]

        # System management menus (leaf nodes route to built-in management pages)
        required_children = [
            "Form Management",
            "Menu Management",
            "Lookup Management",
            "User Management",
        ]
        existing = {
            m.Name
            for m in session.execute(
                select(models.Menu).where(models.Menu.ParentId == root_menu_id)
            ).scalars().all()
        }
        for name in required_children:
            if name not in existing:
                session.add(models.Menu(Name=name, ParentId=root_menu_id, FormId=None))


def apply_migrations() -> None:
    """Apply additive migrations for existing SQLite databases.

    SQLAlchemy's `create_all` does not add columns to existing tables.
    For this prototype we support safe, additive migrations (ALTER TABLE ADD COLUMN).
    """

    engine = get_engine()
    insp = inspect(engine)
    tables = set(insp.get_table_names())

    def ensure_column(table: str, column: str, ddl_type: str) -> None:
        if table not in tables:
            return
        cols = {c["name"] for c in insp.get_columns(table)}
        if column in cols:
            return
        with engine.begin() as conn:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type}"))

    # v1: Lookup.Name
    ensure_column("Lookup", "Name", "VARCHAR(150)")
    with engine.begin() as conn:
        # Backfill Name from Description if missing
        conn.execute(text("UPDATE Lookup SET Name = Description WHERE Name IS NULL OR TRIM(Name) = ''"))

    # v1: FormField.TargetTableName
    ensure_column("FormField", "TargetTableName", "VARCHAR(150)")


def init_db() -> None:
    create_all_tables()
    apply_migrations()
    ensure_admin_and_system_seed()



