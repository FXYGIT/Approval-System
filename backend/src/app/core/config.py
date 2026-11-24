import os
from dataclasses import dataclass, field
from functools import lru_cache

from sqlalchemy import URL


@dataclass(frozen=True)
class AuthSettings:
    secret: str = field(repr=False)
    expire_minutes: int = 60


@lru_cache
def auth_settings() -> AuthSettings:
    secret = os.getenv("JWT_SECRET_KEY", "")
    if len(secret.encode("utf-8")) < 32 or secret.startswith("replace_"):
        raise RuntimeError("JWT_SECRET_KEY must be a random secret of at least 32 bytes")
    minutes = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
    if not 1 <= minutes <= 1440:
        raise RuntimeError("JWT_EXPIRE_MINUTES must be between 1 and 1440")
    return AuthSettings(secret, minutes)


def database_url() -> str | URL:
    if value := os.getenv("DATABASE_URL"):
        return value
    return URL.create(
        "mysql+pymysql",
        username=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_PASSWORD"],
        host=os.getenv("MYSQL_HOST", "mysql"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        database=os.environ["MYSQL_DATABASE"],
        query={"charset": "utf8mb4"},
    )
