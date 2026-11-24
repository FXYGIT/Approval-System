from uuid import uuid4

import pytest
from sqlalchemy import delete, update

from app.db.session import SessionLocal
from app.models import Request, User
from app.repositories import requests


@pytest.mark.parametrize("change", ["version", "status"])
def test_update_and_delete_reject_changes_after_read(change):
    # Deliberately commit isolated probe rows so two real connections can observe them.
    # Always remove only this test's UUIDs, including after failed assertions.
    owner, approver, request_id = (str(uuid4()) for _ in range(3))
    try:
        with SessionLocal.begin() as session:
            session.add_all(
                [
                    User(
                        id=value,
                        username=value,
                        password_hash="test-only",
                        display_name="conflict probe",
                    )
                    for value in (owner, approver)
                ]
            )
            session.flush()
            session.add(
                Request(
                    id=request_id,
                    title="original",
                    content="original",
                    applicant_id=owner,
                    first_approver_id=approver,
                    second_approver_id=approver,
                )
            )
        with SessionLocal() as stale:
            row = requests.by_id(stale, request_id)
            assert row.version == 1 and row.status == "Draft"
            with SessionLocal.begin() as winner:
                values = (
                    {"title": "winner", "version": 2}
                    if change == "version"
                    else {"status": "InProgress", "current_step": "First"}
                )
                winner.execute(update(Request).where(Request.id == request_id).values(**values))
            assert requests.update_draft(stale, row, 1, {"title": "loser"}) == 0
            assert requests.delete_draft(stale, row) == 0
            stale.rollback()
        with SessionLocal() as verification:
            row = verification.get(Request, request_id)
            assert row is not None
            if change == "version":
                assert row.version == 2 and row.title == "winner"
            else:
                assert row.status == "InProgress" and row.current_step == "First"
    finally:
        with SessionLocal.begin() as cleanup:
            cleanup.execute(delete(Request).where(Request.id == request_id))
            cleanup.execute(delete(User).where(User.id.in_([owner, approver])))
