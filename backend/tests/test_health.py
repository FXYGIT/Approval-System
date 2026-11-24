from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.db.session import get_session
from app.main import app


def test_health_uses_database():
    with TestClient(app) as client:
        assert client.get("/api/health").json() == {"status": "ok", "database": "ok"}


def test_database_failure_is_sanitized():
    class UnavailableSession:
        def execute(self, statement):
            raise OperationalError("private SQL", {}, Exception("private password"))

    app.dependency_overrides[get_session] = lambda: UnavailableSession()
    try:
        response = TestClient(app).get("/api/health")
        assert response.status_code == 503
        assert response.json() == {"error": {"code": "HTTP_503", "message": "服务暂不可用"}}
    finally:
        app.dependency_overrides.clear()
