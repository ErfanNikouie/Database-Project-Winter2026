from __future__ import annotations

from functools import lru_cache

from django.conf import settings
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    db_settings = settings.DATABASES["default"]
    django_engine = db_settings["ENGINE"]

    if django_engine.endswith("sqlite3"):
        database = db_settings["NAME"]
        url = f"sqlite:///{database}"
    else:
        user = db_settings["USER"]
        password = db_settings["PASSWORD"]
        host = db_settings["HOST"]
        port = db_settings["PORT"]
        name = db_settings["NAME"]
        url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"

    return create_engine(url, pool_pre_ping=True, future=True)

