from uuid import uuid4

import pytest
from sqlalchemy import insert, inspect
from sqlalchemy.exc import IntegrityError, OperationalError

from app.db.session import engine
from app.models import ApprovalHistory, Request, User


@pytest.fixture
def connection():
    with engine.connect() as conn:
        transaction = conn.begin()
        yield conn
        transaction.rollback()


@pytest.fixture
def request_values(connection):
    applicant, approver = str(uuid4()), str(uuid4())
    for user_id in (applicant, approver):
        connection.execute(
            insert(User).values(
                id=user_id, username=user_id, password_hash="test-only", display_name="测试用户"
            )
        )
    return {
        "title": "测试申请",
        "content": "内容",
        "applicant_id": applicant,
        "first_approver_id": approver,
        "second_approver_id": approver,
    }


@pytest.mark.parametrize(
    ("status", "step"),
    [
        ("Draft", None),
        ("InProgress", "First"),
        ("InProgress", "Second"),
        ("Approved", None),
        ("Rejected", None),
    ],
)
def test_valid_status_step(connection, request_values, status, step):
    connection.execute(insert(Request).values(**request_values, status=status, current_step=step))


@pytest.mark.parametrize(
    ("status", "step"),
    [
        ("InProgress", None),
        ("Draft", "First"),
        ("Approved", "Second"),
        ("Rejected", "First"),
        ("Unknown", None),
        ("InProgress", "Third"),
        ("draft", None),
    ],
)
def test_invalid_status_step_rejected(connection, request_values, status, step):
    with pytest.raises((IntegrityError, OperationalError)):
        connection.execute(
            insert(Request).values(**request_values, status=status, current_step=step)
        )


@pytest.mark.parametrize("field", ["first_approver_id", "second_approver_id", "version"])
def test_request_checks(connection, request_values, field):
    request_values[field] = 0 if field == "version" else request_values["applicant_id"]
    with pytest.raises((IntegrityError, OperationalError)):
        connection.execute(insert(Request).values(**request_values))


def test_foreign_key_restrict_and_username_unique(connection, request_values):
    connection.execute(insert(Request).values(**request_values))
    with pytest.raises(IntegrityError):
        connection.execute(User.__table__.delete().where(User.id == request_values["applicant_id"]))
    with pytest.raises(IntegrityError):
        connection.execute(
            insert(User).values(
                username=request_values["applicant_id"],
                password_hash="test-only",
                display_name="重复",
            )
        )
    request_values["first_approver_id"] = str(uuid4())
    with pytest.raises(IntegrityError):
        connection.execute(insert(Request).values(**request_values))


def test_history_relationships_and_invalid_action(connection, request_values):
    request_id = str(uuid4())
    connection.execute(insert(Request).values(id=request_id, **request_values))
    values = {
        "request_id": request_id,
        "operator_id": request_values["applicant_id"],
        "new_status": "InProgress",
        "new_step": "First",
    }
    connection.execute(insert(ApprovalHistory).values(action="Submit", **values))
    with pytest.raises((IntegrityError, OperationalError)):
        connection.execute(insert(ApprovalHistory).values(action="Delete", **values))
    values["request_id"] = str(uuid4())
    with pytest.raises(IntegrityError):
        connection.execute(insert(ApprovalHistory).values(action="Submit", **values))


def test_tables_indexes_and_microseconds():
    inspector = inspect(engine)
    assert set(inspector.get_table_names()) == {
        "users",
        "requests",
        "approval_histories",
        "alembic_version",
    }
    assert {tuple(index["column_names"]) for index in inspector.get_indexes("requests")} >= {
        ("applicant_id", "created_at", "id"),
        ("first_approver_id", "status", "current_step", "created_at", "id"),
        ("second_approver_id", "status", "current_step", "created_at", "id"),
    }
    assert (
        next(c for c in inspector.get_columns("users") if c["name"] == "created_at")["type"].fsp
        == 6
    )
