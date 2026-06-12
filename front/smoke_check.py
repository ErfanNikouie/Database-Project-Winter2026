"""Local harness to verify Dash frontend modules and API clients import correctly."""

from api.base import DEFAULT_BASE_URL, DEFAULT_TIMEOUT
from layouts.main_layout import build_main_layout
from services.cache_service import cache
from services.session import default_auth_store, default_ui_store
from utils.models import DataListPayload, LoginPayload


def run_smoke_check() -> None:
    LoginPayload(username="demo", password="demo")
    DataListPayload(menu="System", limit=50, offset=0)

    cache.clear()
    _ = build_main_layout()
    auth = default_auth_store()
    ui = default_ui_store()

    print("Dash frontend smoke check passed")
    print(f"Backend URL default: {DEFAULT_BASE_URL}")
    print(f"Request timeout default: {DEFAULT_TIMEOUT}s")
    print(f"Default auth payload keys: {sorted(auth.keys())}")
    print(f"Default UI payload keys: {sorted(ui.keys())}")


if __name__ == "__main__":
    run_smoke_check()

