from django.conf import settings
from django.db import models


class Menu(models.Model):
    name = models.CharField(max_length=120)
    parent_menu = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="children")
    form = models.ForeignKey("forms.Form", null=True, blank=True, on_delete=models.PROTECT, related_name="menus")
    sort_order = models.IntegerField(default=0)
    is_system = models.BooleanField(default=False)

    class Meta:
        db_table = "menu"
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return self.name


class Permission(models.Model):
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name="permissions")
    group = models.ForeignKey("users.UserGroup", on_delete=models.CASCADE, related_name="permissions")
    can_view = models.BooleanField(default=False)
    can_insert = models.BooleanField(default=False)
    can_update = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_print = models.BooleanField(default=False)

    class Meta:
        db_table = "permission"
        unique_together = ("menu", "group")

    def delete(self, using=None, keep_parents=False):
        root_group = settings.HRMS["ROOT_GROUP_NAME"]
        if self.group.name == root_group:
            raise ValueError("Protected permissions cannot be deleted")
        return super().delete(using=using, keep_parents=keep_parents)

