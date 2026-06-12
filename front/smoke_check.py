"""Local harness to verify critical frontend modules and config load correctly."""

from api.base import DEFAULT_BASE_URL, DEFAULT_TIMEOUT
from api.forms import get_form_schema
from services.metadata import clear_metadata_cache
from utils.models import DataListPayload, LoginPayload


def run_smoke_check() -> None:
    LoginPayload(username="demo", password="demo")
    DataListPayload(menu="System", limit=50, offset=0)
    clear_metadata_cache()

    print("Frontend smoke check passed")
    print(f"Backend URL default: {DEFAULT_BASE_URL}")
    print(f"Request timeout default: {DEFAULT_TIMEOUT}s")
    print(f"Schema client loaded: {get_form_schema.__name__}")


if __name__ == "__main__":
    run_smoke_check()

