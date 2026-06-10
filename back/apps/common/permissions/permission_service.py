from apps.common.exceptions import PermissionDeniedException
from apps.forms.models import Form
from apps.menus.models import Permission


class PermissionService:
    OPERATION_MAP = {
        "insert": "can_insert",
        "update": "can_update",
        "delete": "can_delete",
        "detail": "can_view",
        "list": "can_view",
    }

    @classmethod
    def assert_table_permission(cls, user, table_name: str, operation: str) -> None:
        if not user or not user.is_authenticated:
            raise PermissionDeniedException("Authentication required")

        if user.is_superuser:
            return

        form = Form.objects.filter(table_name=table_name).first()
        if not form:
            raise PermissionDeniedException("Form metadata not found")

        menu_ids = list(form.menus.values_list("id", flat=True))
        if not menu_ids:
            raise PermissionDeniedException("No menu is bound to this form")

        group_ids = list(user.groups_ref.values_list("id", flat=True))
        if not group_ids:
            raise PermissionDeniedException("User has no group assigned")

        permission_field = cls.OPERATION_MAP[operation]
        permission_qs = Permission.objects.filter(menu_id__in=menu_ids, group_id__in=group_ids)
        if not permission_qs.filter(**{permission_field: True}).exists():
            raise PermissionDeniedException("User is not authorized for this operation")

