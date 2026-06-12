from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class ApiError(Exception):
    def __init__(self, message: str, field: str | None = None, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        self.field = field
        self.status_code = status_code


class LoginPayload(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class TargetPayload(BaseModel):
    menu: str | None = None
    form: str | None = None

    @model_validator(mode="after")
    def validate_target(self) -> "TargetPayload":
        if bool(self.menu) == bool(self.form):
            raise ValueError("Exactly one of menu or form must be provided")
        return self


class DataListPayload(TargetPayload):
    limit: int = Field(default=50, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
    sort_by: str = "id"
    sort_direction: Literal["asc", "desc"] = "asc"
    filters: dict[str, Any] = Field(default_factory=dict)


class DataWritePayload(TargetPayload):
    data: dict[str, Any]


class DetailPayload(TargetPayload):
    id: int = Field(ge=1)


class ProfileUpdatePayload(BaseModel):
    username: str | None = None
    current_password: str | None = None
    new_password: str | None = None
    confirm_new_password: str | None = None

