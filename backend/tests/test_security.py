from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient
from helpers import draft_payload
from sqlalchemy import func, select

from app.core.config import auth_settings
from app.core.security import AUDIENCE, ISSUER, create_access_token
from app.main import app
from app.models import Request, User
from app.repositories import requests


@pytest.mark.parametrize(
    "kind",
    [
        "expired",
        "tampered",
        "wrong-algorithm",
        "missing-exp",
        "invalid-sub",
        "missing-user",
        "wrong-audience",
        "wrong-issuer",
        "wrong-type",
        "future-iat",
    ],
)
def test_invalid_tokens(api, actors, kind):
    client, _ = api
    now = datetime.now(UTC)
    claims = {
        "sub": actors[0][0]["id"],
        "exp": now + timedelta(minutes=10),
        "iat": now,
        "iss": ISSUER,
        "aud": AUDIENCE,
        "type": "access",
    }
    key, algorithm = auth_settings().secret, "HS256"
    if kind == "expired":
        claims["exp"] = now - timedelta(seconds=10)
    elif kind == "tampered":
        key = "untrusted-signing-key" * 4
    elif kind == "wrong-algorithm":
        algorithm = "HS512"
    elif kind == "missing-exp":
        del claims["exp"]
    elif kind == "invalid-sub":
        claims["sub"] = "not-a-uuid"
    elif kind == "missing-user":
        claims["sub"] = str(uuid4())
    elif kind == "wrong-audience":
        claims["aud"] = "another-api"
    elif kind == "wrong-issuer":
        claims["iss"] = "another-issuer"
    elif kind == "wrong-type":
        claims["type"] = "refresh"
    elif kind == "future-iat":
        claims["iat"] = now + timedelta(hours=1)
    token = jwt.encode(claims, key, algorithm=algorithm)
    response = client.get("/api/users/me", headers={"Authorization": "Bearer " + token})
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json()["error"]["code"] == "INVALID_TOKEN"


def test_token_claims_and_lifetime():
    user_id = str(uuid4())
    token, expires = create_access_token(user_id)
    claims = jwt.decode(token, auth_settings().secret, algorithms=["HS256"], audience=AUDIENCE)
    assert claims["sub"] == user_id
    assert claims["exp"] - claims["iat"] == expires == auth_settings().expire_minutes * 60


@pytest.mark.parametrize(
    "secret", ["", "short", "replace_with_a_random_secret_of_at_least_32_bytes"]
)
def test_invalid_secret_fails_startup(monkeypatch, secret):
    auth_settings.cache_clear()
    monkeypatch.setenv("JWT_SECRET_KEY", secret)
    try:
        with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"), TestClient(app):
            pass
    finally:
        auth_settings.cache_clear()


def test_database_write_failure_rolls_back_and_hides_details(api, actors, monkeypatch, caplog):
    client, session = api
    original_add = requests.add

    def failing_add(session, row):
        original_add(session, row)
        raise RuntimeError("private-password private-SQL")

    monkeypatch.setattr(requests, "add", failing_add)
    response = client.post("/api/requests", headers=actors[0][1], json=draft_payload(actors))
    assert response.status_code == 500
    assert response.json() == {"error": {"code": "INTERNAL_ERROR", "message": "服务内部错误"}}
    assert "private-password" not in caplog.text and "private-SQL" not in caplog.text
    assert "Unhandled request failure: RuntimeError" in caplog.text
    assert all(record.exc_info is None for record in caplog.records)
    assert (
        session.scalar(
            select(func.count())
            .select_from(Request)
            .where(Request.applicant_id == actors[0][0]["id"])
        )
        == 0
    )
    assert session.get(User, actors[0][0]["id"]) is not None


def test_openapi_security_and_contract():
    schema = app.openapi()
    for path in ("/api/users/me", "/api/users", "/api/requests", "/api/requests/{request_id}"):
        for operation in schema["paths"][path].values():
            assert operation["security"] == [{"HTTPBearer": []}]
            assert operation["responses"]["422"]["content"]["application/json"]["schema"] == {
                "$ref": "#/components/schemas/ErrorResponse"
            }
    for path in ("/api/auth/login", "/api/auth/register"):
        assert not schema["paths"][path]["post"].get("security")
    draft = schema["components"]["schemas"]["DraftInput"]
    assert set(draft["properties"]) == {"title", "content", "firstApproverId", "secondApproverId"}
    assert draft["additionalProperties"] is False
    assert all(
        "password" not in name.lower()
        for name in schema["components"]["schemas"]["UserPublic"]["properties"]
    )
