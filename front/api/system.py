from __future__ import annotations

from api.base import request_json


def get_metadata_version(*, base_url: str, access_token: str) -> str:
    data = request_json(
        method="GET",
        path="/api/system/metadata/version",
        base_url=base_url,
        access_token=access_token,
    )
    return str(data.get("version", ""))

