from uuid import uuid4

import pytest
from helpers import draft_payload, register
from sqlalchemy import delete, func, select, update

from app.db.session import SessionLocal
from app.models import ApprovalHistory, Request, User
from app.repositories import history as history_repo
from app.repositories import requests as requests_repo


def make_draft(client, actors):
    payload = draft_payload(actors) | {"secondApproverId": actors[2][0]["id"]}
    created = client.post("/api/requests", headers=actors[0][1], json=payload)
    assert created.status_code == 201, created.text
    return created.json()["id"]


def make_submitted(client, actors):
    rid = make_draft(client, actors)
    submitted = client.post(f"/api/requests/{rid}/submit", headers=actors[0][1])
    assert submitted.status_code == 200, submitted.text
    return rid, submitted.json()


def history_actions(client, actors, rid):
    resp = client.get(f"/api/requests/{rid}/history", headers=actors[0][1])
    assert resp.status_code == 200, resp.text
    return [e["action"] for e in resp.json()]


def test_approval_endpoints_require_auth(api):
    client, _ = api
    rid = str(uuid4())
    cases = [
        ("post", f"/api/requests/{rid}/submit", None),
        ("post", f"/api/requests/{rid}/approve", {}),
        ("post", f"/api/requests/{rid}/reject", {"comment": "x"}),
        ("get", f"/api/requests/{rid}/history", None),
    ]
    for method, path, body in cases:
        assert client.request(method, path, json=body).status_code == 401


def test_submit_transitions_and_writes_history(api, actors):
    client, _ = api
    rid, body = make_submitted(client, actors)
    assert (body["status"], body["currentStep"], body["version"]) == ("InProgress", "First", 2)
    assert body["submittedAt"] is not None
    entries = client.get(f"/api/requests/{rid}/history", headers=actors[0][1]).json()
    assert len(entries) == 1
    first = entries[0]
    assert first["action"] == "Submit"
    assert first["operator"]["id"] == actors[0][0]["id"]
    assert first["step"] is None and first["previousStep"] is None
    assert first["previousStatus"] == "Draft"
    assert first["newStatus"] == "InProgress" and first["newStep"] == "First"


def test_submit_requires_applicant(api, actors):
    client, _ = api
    rid = make_draft(client, actors)
    for actor in (actors[1], actors[2]):
        assert client.post(f"/api/requests/{rid}/submit", headers=actor[1]).status_code == 403


@pytest.mark.parametrize(
    ("status", "step"), [("InProgress", "First"), ("Approved", None), ("Rejected", None)]
)
def test_submit_non_draft_rejected(api, actors, status, step):
    client, session = api
    rid, _ = make_submitted(client, actors)
    session.execute(
        update(Request).where(Request.id == rid).values(status=status, current_step=step)
    )
    session.commit()
    assert client.post(f"/api/requests/{rid}/submit", headers=actors[0][1]).status_code == 409


def test_first_approve_advances_to_second(api, actors):
    client, _ = api
    rid, _ = make_submitted(client, actors)
    approved = client.post(
        f"/api/requests/{rid}/approve", headers=actors[1][1], json={"comment": "同意"}
    )
    assert approved.status_code == 200, approved.text
    assert (
        approved.json()["status"],
        approved.json()["currentStep"],
        approved.json()["version"],
    ) == (
        "InProgress",
        "Second",
        3,
    )
    assert history_actions(client, actors, rid) == ["Submit", "FirstApprove"]


def test_second_approve_completes(api, actors):
    client, _ = api
    rid, _ = make_submitted(client, actors)
    client.post(f"/api/requests/{rid}/approve", headers=actors[1][1], json={"comment": "同意"})
    approved = client.post(f"/api/requests/{rid}/approve", headers=actors[2][1], json={})
    assert approved.status_code == 200, approved.text
    assert (
        approved.json()["status"],
        approved.json()["currentStep"],
        approved.json()["version"],
    ) == (
        "Approved",
        None,
        4,
    )
    assert history_actions(client, actors, rid) == ["Submit", "FirstApprove", "SecondApprove"]


@pytest.mark.parametrize("actor_idx", [0, 2])
@pytest.mark.parametrize("method", ["approve", "reject"])
def test_non_current_approver_cannot_operate(api, actors, actor_idx, method):
    client, _ = api
    rid, _ = make_submitted(client, actors)
    body = {"comment": "x"} if method == "reject" else {}
    resp = client.post(f"/api/requests/{rid}/{method}", headers=actors[actor_idx][1], json=body)
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "APPROVAL_NOT_ASSIGNED"


def test_reject_requires_comment(api, actors):
    client, _ = api
    rid, _ = make_submitted(client, actors)
    for body in ({}, {"comment": "   "}, {"comment": "x" * 501}):
        resp = client.post(f"/api/requests/{rid}/reject", headers=actors[1][1], json=body)
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_first_reject_ends_flow(api, actors):
    client, _ = api
    rid, _ = make_submitted(client, actors)
    rejected = client.post(
        f"/api/requests/{rid}/reject", headers=actors[1][1], json={"comment": "材料不全"}
    )
    assert rejected.status_code == 200, rejected.text
    assert (
        rejected.json()["status"],
        rejected.json()["currentStep"],
        rejected.json()["version"],
    ) == (
        "Rejected",
        None,
        3,
    )
    assert (
        client.post(f"/api/requests/{rid}/approve", headers=actors[2][1], json={}).status_code
        == 409
    )
    assert history_actions(client, actors, rid) == ["Submit", "FirstReject"]


def test_second_reject_ends_flow(api, actors):
    client, _ = api
    rid, _ = make_submitted(client, actors)
    client.post(f"/api/requests/{rid}/approve", headers=actors[1][1], json={})
    rejected = client.post(
        f"/api/requests/{rid}/reject", headers=actors[2][1], json={"comment": "不同意"}
    )
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["status"] == "Rejected"
    assert history_actions(client, actors, rid) == ["Submit", "FirstApprove", "SecondReject"]


def test_operate_after_approved_rejected(api, actors):
    client, _ = api
    rid, _ = make_submitted(client, actors)
    client.post(f"/api/requests/{rid}/approve", headers=actors[1][1], json={})
    client.post(f"/api/requests/{rid}/approve", headers=actors[2][1], json={})
    for method, body in (("approve", {}), ("reject", {"comment": "x"})):
        resp = client.post(f"/api/requests/{rid}/{method}", headers=actors[2][1], json=body)
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "INVALID_REQUEST_STATE"


def test_approve_with_stale_version_conflicts(api, actors):
    client, _ = api
    rid, _ = make_submitted(client, actors)
    stale = client.post(f"/api/requests/{rid}/approve", headers=actors[1][1], json={"version": 1})
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "APPROVAL_CONFLICT"
    ok = client.post(f"/api/requests/{rid}/approve", headers=actors[1][1], json={"version": 2})
    assert ok.status_code == 200


def test_history_ordering_and_permission(api, actors):
    client, _ = api
    rid, _ = make_submitted(client, actors)
    client.post(f"/api/requests/{rid}/approve", headers=actors[1][1], json={})
    client.post(f"/api/requests/{rid}/approve", headers=actors[2][1], json={})
    entries = client.get(f"/api/requests/{rid}/history", headers=actors[0][1]).json()
    assert [e["step"] for e in entries] == [None, "First", "Second"]
    assert [e["operator"]["id"] for e in entries] == [
        actors[0][0]["id"],
        actors[1][0]["id"],
        actors[2][0]["id"],
    ]
    stranger = register(client)[1]
    assert client.get(f"/api/requests/{rid}/history", headers=stranger).status_code == 403


def test_pending_list_scoped(api, actors):
    client, _ = api
    make_draft(client, actors)  # draft must not appear in pending
    rid, _ = make_submitted(client, actors)
    assert (
        client.get("/api/requests", headers=actors[1][1], params={"scope": "pending"}).json()[
            "total"
        ]
        == 1
    )
    for actor in (actors[0], actors[2]):
        assert (
            client.get("/api/requests", headers=actor[1], params={"scope": "pending"}).json()[
                "total"
            ]
            == 0
        )
    client.post(f"/api/requests/{rid}/approve", headers=actors[1][1], json={})
    assert (
        client.get("/api/requests", headers=actors[2][1], params={"scope": "pending"}).json()[
            "total"
        ]
        == 1
    )
    assert (
        client.get("/api/requests", headers=actors[1][1], params={"scope": "pending"}).json()[
            "total"
        ]
        == 0
    )
    client.post(f"/api/requests/{rid}/approve", headers=actors[2][1], json={})
    for actor in actors:
        assert (
            client.get("/api/requests", headers=actor[1], params={"scope": "pending"}).json()[
                "total"
            ]
            == 0
        )


def test_history_write_failure_rolls_back(api, actors, monkeypatch):
    client, session = api
    rid, _ = make_submitted(client, actors)
    original_add = history_repo.add

    def failing_add(session, history_row):
        original_add(session, history_row)
        raise RuntimeError("history-write-failure")

    monkeypatch.setattr(history_repo, "add", failing_add)
    resp = client.post(f"/api/requests/{rid}/approve", headers=actors[1][1], json={})
    assert resp.status_code == 500
    session.expire_all()
    row = session.get(Request, rid)
    assert (row.status, row.current_step, row.version) == ("InProgress", "First", 2)
    assert (
        session.scalar(
            select(func.count())
            .select_from(ApprovalHistory)
            .where(ApprovalHistory.request_id == rid)
        )
        == 1
    )


def test_concurrent_approval_single_winner():
    owner, first, second, request_id = (str(uuid4()) for _ in range(4))
    try:
        with SessionLocal.begin() as session:
            session.add_all(
                [
                    User(id=owner, username=owner, password_hash="test", display_name="owner"),
                    User(id=first, username=first, password_hash="test", display_name="first"),
                    User(id=second, username=second, password_hash="test", display_name="second"),
                ]
            )
            session.flush()
            session.add(
                Request(
                    id=request_id,
                    title="t",
                    content="c",
                    applicant_id=owner,
                    first_approver_id=first,
                    second_approver_id=second,
                    status="InProgress",
                    current_step="First",
                )
            )
            session.flush()
            # version_id_col forces version=1 on INSERT; simulate the submit transition via Core UPDATE
            session.execute(update(Request).where(Request.id == request_id).values(version=2))
        with SessionLocal() as a, SessionLocal() as b:
            row_a = requests_repo.by_id(a, request_id)
            row_b = requests_repo.by_id(b, request_id)
            assert row_a.version == 2 and row_b.version == 2
            assert (
                requests_repo.advance_approval(a, row_a, first, "First", "InProgress", "Second")
                == 1
            )
            a.commit()
            assert (
                requests_repo.advance_approval(b, row_b, first, "First", "InProgress", "Second")
                == 0
            )
            b.rollback()
        with SessionLocal() as verification:
            row = verification.get(Request, request_id)
            assert row.status == "InProgress" and row.current_step == "Second" and row.version == 3
    finally:
        with SessionLocal.begin() as cleanup:
            cleanup.execute(delete(Request).where(Request.id == request_id))
            cleanup.execute(delete(User).where(User.id.in_([owner, first, second])))
