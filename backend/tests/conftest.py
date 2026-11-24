import pytest
from fastapi.testclient import TestClient
from helpers import register
from sqlalchemy.orm import Session

from app.db.session import engine, get_session
from app.main import app


@pytest.fixture
def api():
    # Services can commit normally; the outer MySQL transaction is always rolled back.
    with engine.connect() as connection:
        transaction = connection.begin()
        with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
            app.dependency_overrides[get_session] = lambda: session
            try:
                with TestClient(app, raise_server_exceptions=True) as client:
                    yield client, session
            finally:
                app.dependency_overrides.clear()
        transaction.rollback()


@pytest.fixture
def actors(api):
    client, _ = api
    return [register(client) for _ in range(3)]
