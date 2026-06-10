from __future__ import annotations

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, username: str, password: str | None = None, **extra_fields):
        if not username:
            raise ValueError("Username is required")
        user = self.model(username=username, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, username: str, password: str, **extra_fields):
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(username=username, password=password, **extra_fields)


class UserGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default="")

    class Meta:
        db_table = "user_group"

    def __str__(self) -> str:
        return self.name


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128, db_column="password_hash")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    groups_ref = models.ManyToManyField(UserGroup, related_name="users", blank=True)

    USERNAME_FIELD = "username"

    objects = UserManager()

    class Meta:
        db_table = "user"

    def delete(self, using=None, keep_parents=False):
        root_username = settings.HRMS["ROOT_USERNAME"]
        if self.username == root_username:
            raise ValueError("Root administrator cannot be deleted")
        return super().delete(using=using, keep_parents=keep_parents)

    def save(self, *args, **kwargs):
        root_username = settings.HRMS["ROOT_USERNAME"]
        if self.username == root_username and not self.is_active:
            raise ValueError("Root administrator cannot be deactivated")
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.username

