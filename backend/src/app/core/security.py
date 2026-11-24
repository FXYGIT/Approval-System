from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import auth_settings
from app.core.exceptions import BusinessError

password_hasher = PasswordHasher()
_dummy_hash = password_hasher.hash("dummy password for missing users")
ISSUER = "approval-system"
AUDIENCE = "approval-api"


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, hashed: str | None) -> bool:
    try:
        valid = password_hasher.verify(hashed or _dummy_hash, password)
        return valid and hashed is not None
    except (VerificationError, InvalidHashError):
        return False


def create_access_token(user_id: str) -> tuple[str, int]:
    settings = auth_settings()
    now = datetime.now(UTC)
    expires = settings.expire_minutes * 60
    token = jwt.encode(
        {
            "sub": user_id,
            "iat": now,
            "exp": now + timedelta(seconds=expires),
            "iss": ISSUER,
            "aud": AUDIENCE,
            "type": "access",
        },
        settings.secret,
        algorithm="HS256",
    )
    return token, expires


def decode_access_token(token: str) -> str:
    try:
        claims = jwt.decode(
            token,
            auth_settings().secret,
            algorithms=["HS256"],
            issuer=ISSUER,
            audience=AUDIENCE,
            options={"require": ["sub", "iat", "exp", "iss", "aud", "type"]},
        )
        if claims["type"] != "access":
            raise ValueError("Invalid token type")
        return str(UUID(claims["sub"]))
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise BusinessError(401, "INVALID_TOKEN", "身份凭证无效或已过期") from None
