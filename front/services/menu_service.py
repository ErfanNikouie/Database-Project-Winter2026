from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from db.database import session_scope
from db.models import Menu


@dataclass
class MenuNode:
    menu: Menu
    children: list["MenuNode"]


class MenuService:
    def list_menus(self) -> list[Menu]:
        with session_scope() as session:
            return session.execute(select(Menu).order_by(Menu.ParentId, Menu.Name)).scalars().all()

    def get_menu(self, menu_id: int) -> Menu | None:
        with session_scope() as session:
            return session.get(Menu, menu_id)

    def build_tree(self) -> list[MenuNode]:
        """Build a forest of menu nodes."""
        menus = self.list_menus()
        by_parent: dict[int | None, list[Menu]] = {}
        for m in menus:
            by_parent.setdefault(m.ParentId, []).append(m)

        def build(parent_id: int | None) -> list[MenuNode]:
            nodes: list[MenuNode] = []
            for m in sorted(by_parent.get(parent_id, []), key=lambda x: x.Name.lower()):
                nodes.append(MenuNode(menu=m, children=build(m.Id)))
            return nodes

        return build(None)

    def create_menu(self, name: str, parent_id: int | None, form_id: int | None) -> Menu:
        with session_scope() as session:
            menu = Menu(Name=name.strip(), ParentId=parent_id, FormId=form_id)
            session.add(menu)
            session.flush()
            return menu

    def update_menu(self, menu_id: int, *, name: str, parent_id: int | None, form_id: int | None) -> None:
        with session_scope() as session:
            menu = session.get(Menu, menu_id)
            if menu is None:
                raise ValueError("Menu not found")
            menu.Name = name.strip()
            menu.ParentId = parent_id
            menu.FormId = form_id

    def delete_menu(self, menu_id: int) -> None:
        with session_scope() as session:
            menu = session.get(Menu, menu_id)
            if menu is None:
                return
            session.delete(menu)

