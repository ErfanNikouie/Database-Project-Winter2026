from __future__ import annotations

from typing import Any

from api.auth import get_current_user, login, logout, refresh_access_token, update_current_user
from api.crud import delete_row, detail_row, insert_row, list_options, list_rows, update_row
from api.forms import get_form_schema
from api.menus import get_menu_tree
from api.reports import get_available_reports, get_report_definition, run_report
from api.system import get_metadata_version


class APIClient:
    def login(self, *, base_url: str, username: str, password: str) -> dict[str, Any]:
        return login(base_url=base_url, username=username, password=password)

    def logout(self, *, base_url: str, access_token: str, refresh_token: str) -> None:
        logout(base_url=base_url, access_token=access_token, refresh_token=refresh_token)

    def refresh_access_token(self, *, base_url: str, refresh_token: str) -> str:
        return refresh_access_token(base_url=base_url, refresh_token=refresh_token)

    def get_current_user(self, *, base_url: str, access_token: str) -> dict[str, Any]:
        return get_current_user(base_url=base_url, access_token=access_token)

    def update_current_user(self, *, base_url: str, access_token: str, payload: dict[str, Any]) -> dict[str, Any]:
        return update_current_user(base_url=base_url, access_token=access_token, payload=payload)

    def get_menu_tree(self, *, base_url: str, access_token: str, etag: str | None) -> tuple[list[dict] | None, str | None]:
        return get_menu_tree(base_url=base_url, access_token=access_token, etag=etag)

    def get_metadata_version(self, *, base_url: str, access_token: str) -> str:
        return get_metadata_version(base_url=base_url, access_token=access_token)

    def get_form_schema(self, *, base_url: str, access_token: str, form_name: str) -> dict[str, Any]:
        return get_form_schema(base_url=base_url, access_token=access_token, form_name=form_name)

    def list_rows(self, *, base_url: str, access_token: str, payload: dict[str, Any]) -> dict[str, Any]:
        return list_rows(base_url=base_url, access_token=access_token, payload=payload)

    def detail_row(self, *, base_url: str, access_token: str, payload: dict[str, Any]) -> dict[str, Any]:
        return detail_row(base_url=base_url, access_token=access_token, payload=payload)

    def insert_row(self, *, base_url: str, access_token: str, payload: dict[str, Any]) -> dict[str, Any]:
        return insert_row(base_url=base_url, access_token=access_token, payload=payload)

    def update_row(self, *, base_url: str, access_token: str, payload: dict[str, Any]) -> dict[str, Any]:
        return update_row(base_url=base_url, access_token=access_token, payload=payload)

    def delete_row(self, *, base_url: str, access_token: str, payload: dict[str, Any]) -> dict[str, Any]:
        return delete_row(base_url=base_url, access_token=access_token, payload=payload)

    def list_options(self, *, base_url: str, access_token: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        return list_options(base_url=base_url, access_token=access_token, payload=payload)

    def get_available_reports(self, *, base_url: str, access_token: str) -> list[dict[str, Any]]:
        return get_available_reports(base_url=base_url, access_token=access_token)

    def run_report(self, *, base_url: str, access_token: str, payload: dict[str, Any]) -> dict[str, Any]:
        return run_report(base_url=base_url, access_token=access_token, payload=payload)

    def get_report_definition(self, *, base_url: str, access_token: str, report_id: int) -> dict[str, Any]:
        return get_report_definition(base_url=base_url, access_token=access_token, report_id=report_id)


api_client = APIClient()

