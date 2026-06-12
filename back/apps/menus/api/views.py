from __future__ import annotations

from collections import defaultdict
import hashlib

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.forms.serializers.data_serializers import ErrorEnvelopeSerializer, GenericSuccessEnvelopeSerializer
from apps.menus.models import Menu, Permission


class MenuTreeAPIView(APIView):
    @extend_schema(
        tags=["Menus"],
        operation_id="menu_tree",
        summary="Return permission-aware hierarchical menu tree for current user",
        responses={
            200: OpenApiResponse(response=GenericSuccessEnvelopeSerializer),
            401: OpenApiResponse(response=ErrorEnvelopeSerializer),
            403: OpenApiResponse(response=ErrorEnvelopeSerializer),
        },
        examples=[
            OpenApiExample(
                "Menu Tree Response",
                value={
                    "success": True,
                    "data": {
                        "items": [
                            {
                                "id": 1,
                                "name": "System",
                                "parent_menu_id": None,
                                "sort_order": 0,
                                "form": None,
                                "permissions": {
                                    "can_view": True,
                                    "can_insert": False,
                                    "can_update": False,
                                    "can_delete": False,
                                    "can_print": False,
                                },
                                "children": [
                                    {
                                        "id": 2,
                                        "name": "Users",
                                        "parent_menu_id": 1,
                                        "sort_order": 1,
                                        "form": None,
                                        "permissions": {
                                            "can_view": True,
                                            "can_insert": False,
                                            "can_update": False,
                                            "can_delete": False,
                                            "can_print": False,
                                        },
                                        "children": [],
                                    }
                                ],
                            }
                        ]
                    },
                },
                response_only=True,
            )
        ],
    )
    def get(self, request):
        etag = self._build_etag(request.user)
        if request.headers.get("If-None-Match") == etag:
            return Response(status=304, headers={"ETag": etag})

        menus = list(
            Menu.objects.select_related("form", "parent_menu").order_by("sort_order", "id")
        )
        permissions = self._build_permissions_map(request.user, menus)

        children_map: dict[int | None, list[Menu]] = defaultdict(list)
        for menu in menus:
            children_map[menu.parent_menu_id].append(menu)

        def build_node(menu: Menu):
            children_nodes = []
            for child in children_map.get(menu.id, []):
                child_node = build_node(child)
                if child_node is not None:
                    children_nodes.append(child_node)

            menu_permissions = permissions.get(
                menu.id,
                {
                    "can_view": False,
                    "can_insert": False,
                    "can_update": False,
                    "can_delete": False,
                    "can_print": False,
                },
            )
            can_view = menu_permissions["can_view"]
            if not can_view and not children_nodes:
                return None

            return {
                "id": menu.id,
                "name": menu.name,
                "parent_menu_id": menu.parent_menu_id,
                "sort_order": menu.sort_order,
                "form": (
                    {
                        "id": menu.form_id,
                        "name": menu.form.name,
                        "table_name": menu.form.table_name,
                        "is_system": menu.form.is_system,
                    }
                    if menu.form_id
                    else None
                ),
                "permissions": menu_permissions,
                "children": children_nodes,
            }

        roots = []
        for root_menu in children_map.get(None, []):
            node = build_node(root_menu)
            if node is not None:
                roots.append(node)

        return Response({"success": True, "data": {"items": roots}}, headers={"ETag": etag})

    @staticmethod
    def _build_permissions_map(user, menus: list[Menu]) -> dict[int, dict[str, bool]]:
        menu_ids = [menu.id for menu in menus]
        if user.is_superuser:
            return {
                menu_id: {
                    "can_view": True,
                    "can_insert": True,
                    "can_update": True,
                    "can_delete": True,
                    "can_print": True,
                }
                for menu_id in menu_ids
            }

        group_ids = list(user.groups_ref.values_list("id", flat=True))
        if not group_ids:
            return {}

        rows = Permission.objects.filter(menu_id__in=menu_ids, group_id__in=group_ids).values(
            "menu_id",
            "can_view",
            "can_insert",
            "can_update",
            "can_delete",
            "can_print",
        )
        result: dict[int, dict[str, bool]] = {}
        for row in rows:
            menu_id = row["menu_id"]
            current = result.setdefault(
                menu_id,
                {
                    "can_view": False,
                    "can_insert": False,
                    "can_update": False,
                    "can_delete": False,
                    "can_print": False,
                },
            )
            current["can_view"] = current["can_view"] or bool(row["can_view"])
            current["can_insert"] = current["can_insert"] or bool(row["can_insert"])
            current["can_update"] = current["can_update"] or bool(row["can_update"])
            current["can_delete"] = current["can_delete"] or bool(row["can_delete"])
            current["can_print"] = current["can_print"] or bool(row["can_print"])
        return result

    @staticmethod
    def _build_etag(user) -> str:
        digest = hashlib.sha256()
        digest.update(str(user.id).encode("utf-8"))
        menu_rows = Menu.objects.order_by("id").values_list(
            "id", "name", "parent_menu_id", "form_id", "sort_order", "is_system"
        )
        for row in menu_rows:
            digest.update(str(tuple(row)).encode("utf-8"))

        permission_rows = Permission.objects.order_by("id").values_list(
            "menu_id", "group_id", "can_view", "can_insert", "can_update", "can_delete", "can_print"
        )
        for row in permission_rows:
            digest.update(str(tuple(row)).encode("utf-8"))

        return digest.hexdigest()

