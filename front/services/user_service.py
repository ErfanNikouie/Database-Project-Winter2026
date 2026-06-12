from __future__ import annotations

from sqlalchemy import select

from db.database import session_scope
from db.models import User, UserGroup


class UserService:
    def list_users(self) -> list[User]:
        with session_scope() as session:
            return session.execute(select(User).order_by(User.Username)).scalars().all()

    def create_user(
        self,
        *,
        username: str,
        password_hash: str,
        is_active: bool,
        access_level: int,
        has_confidential_access: bool,
    ) -> User:
        with session_scope() as session:
            u = User(
                Username=username.strip(),
                PasswordHash=password_hash,
                IsActive=bool(is_active),
                AccessLevel=int(access_level),
                HasConfidentialAccess=bool(has_confidential_access),
            )
            session.add(u)
            session.flush()
            return u

    def update_user(
        self,
        user_id: int,
        *,
        username: str,
        password_hash: str | None,
        is_active: bool,
        access_level: int,
        has_confidential_access: bool,
    ) -> None:
        with session_scope() as session:
            u = session.get(User, user_id)
            if u is None:
                raise ValueError("User not found")
            u.Username = username.strip()
            if password_hash:
                u.PasswordHash = password_hash
            u.IsActive = bool(is_active)
            u.AccessLevel = int(access_level)
            u.HasConfidentialAccess = bool(has_confidential_access)

    def delete_user(self, user_id: int) -> None:
        with session_scope() as session:
            u = session.get(User, user_id)
            if u is None:
                return
            if u.Id == 0:
                raise ValueError("Cannot delete admin")
            session.delete(u)

    def list_groups(self) -> list[UserGroup]:
        with session_scope() as session:
            return session.execute(select(UserGroup).order_by(UserGroup.Name)).scalars().all()

    def create_group(self, *, name: str, description: str | None) -> UserGroup:
        with session_scope() as session:
            g = UserGroup(Name=name.strip(), Description=description or None)
            session.add(g)
            session.flush()
            return g

    def update_group(self, group_id: int, *, name: str, description: str | None) -> None:
        with session_scope() as session:
            g = session.get(UserGroup, group_id)
            if g is None:
                raise ValueError("Group not found")
            g.Name = name.strip()
            g.Description = description or None

    def delete_group(self, group_id: int) -> None:
        with session_scope() as session:
            g = session.get(UserGroup, group_id)
            if g is None:
                return
            session.delete(g)

