from __future__ import annotations

from sqlalchemy import select

from db.database import session_scope
from db.models import Lookup, LookupValues


class LookupService:
    def list_lookups(self) -> list[Lookup]:
        with session_scope() as session:
            return session.execute(select(Lookup).order_by(Lookup.Name, Lookup.Description)).scalars().all()

    def get_lookup(self, lookup_id: int) -> Lookup | None:
        with session_scope() as session:
            return session.get(Lookup, lookup_id)

    def create_lookup(self, *, name: str, description: str) -> Lookup:
        with session_scope() as session:
            l = Lookup(Name=name.strip() if name else None, Description=description.strip())
            session.add(l)
            session.flush()
            return l

    def update_lookup(self, lookup_id: int, *, name: str, description: str) -> None:
        with session_scope() as session:
            l = session.get(Lookup, lookup_id)
            if l is None:
                raise ValueError("Lookup not found")
            l.Name = name.strip() if name else None
            l.Description = description.strip()

    def delete_lookup(self, lookup_id: int) -> None:
        with session_scope() as session:
            l = session.get(Lookup, lookup_id)
            if l is None:
                return
            session.delete(l)

    def list_values(self, lookup_id: int) -> list[LookupValues]:
        with session_scope() as session:
            return session.execute(
                select(LookupValues).where(LookupValues.LookupId == lookup_id).order_by(LookupValues.Value)
            ).scalars().all()

    def create_value(self, lookup_id: int, value: str) -> LookupValues:
        with session_scope() as session:
            lv = LookupValues(LookupId=lookup_id, Value=value.strip())
            session.add(lv)
            session.flush()
            return lv

    def update_value(self, value_id: int, *, value: str) -> None:
        with session_scope() as session:
            lv = session.get(LookupValues, value_id)
            if lv is None:
                raise ValueError("LookupValue not found")
            lv.Value = value.strip()

    def delete_value(self, value_id: int) -> None:
        with session_scope() as session:
            lv = session.get(LookupValues, value_id)
            if lv is None:
                return
            session.delete(lv)

