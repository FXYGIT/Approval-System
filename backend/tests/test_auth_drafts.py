from uuid import uuid4

import pytest
from helpers import draft_payload, register
from sqlalchemy import func, select, update

from app.models import ApprovalHistory, Request, User


@pytest.mark.parametrize("method", ["post", "put", "delete"])
def test_write_requires_authentication(api, method):
    client, _ = api
    path = "/api/requests" if method == "post" else "/api/requests/" + str(uuid4())
    assert client.request(method, path, json={}).status_code == 401


@pytest.mark.parametrize(
    "changes",
    [
        {"applicantId": str(uuid4())},
        {"status": "Approved"},
        {"currentStep": "First"},
        {"first_approver_id": str(uuid4())},
        {"version": 0},
        {"version": True},
    ],
)
def test_edit_rejects_forgery_and_invalid_version(api, actors, changes):
    client, session = api
    payload = draft_payload(actors)
    response = client.post("/api/requests", headers=actors[0][1], json=payload)
    request_id = response.json()["id"]
    response = client.put(
        "/api/requests/" + request_id, headers=actors[0][1], json=payload | {"version": 1} | changes
    )
    assert response.status_code == 422
    session.expire_all()
    row = session.get(Request, request_id)
    assert row.applicant_id == actors[0][0]["id"] and row.status == "Draft" and row.version == 1


def test_distinct_second_approver_can_read_but_not_edit(api, actors):
    client, _ = api
    payload = draft_payload(actors) | {"secondApproverId": actors[2][0]["id"]}
    response = client.post("/api/requests", headers=actors[0][1], json=payload)
    path = "/api/requests/" + response.json()["id"]
    assert client.get(path, headers=actors[2][1]).status_code == 200
    assert client.put(path, headers=actors[2][1], json=payload | {"version": 1}).status_code == 403


def test_registration_login_me_and_hash(api):
    client, session = api
    user, headers = register(client)
    assert set(user) == {"id", "username", "displayName", "createdAt"}
    assert user["createdAt"].endswith("Z")
    assert client.get("/api/users/me", headers=headers).json() == user
    stored = session.get(User, user["id"])
    assert stored.password_hash.startswith("$argon2id$")
    assert stored.password_hash != " password-123 "
    duplicate = client.post(
        "/api/auth/register",
        json={"username": user["username"], "password": "another-secret", "displayName": "其他人"},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "USERNAME_ALREADY_EXISTS"
    for username, password in [(user["username"], "password-123"), ("missing-user", "wrong-pass")]:
        response = client.post("/api/auth/login", json={"username": username, "password": password})
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert session.scalar(select(func.count()).select_from(User).where(User.id == user["id"])) == 1


@pytest.mark.parametrize("path", ["/api/users/me", "/api/users", "/api/requests"])
@pytest.mark.parametrize("header", [None, "Basic nonsense", "Bearer broken.token.value"])
def test_authentication_required(api, path, header):
    client, _ = api
    response = client.get(path, headers={"Authorization": header} if header else {})
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "changes",
    [
        {"password": "short"},
        {"password": "x" * 129},
        {"username": "   "},
        {"username": "x" * 51},
        {"displayName": " "},
        {"displayName": "x" * 101},
        {"role": "admin"},
    ],
)
def test_registration_validation_does_not_echo_password(api, changes):
    client, _ = api
    body = {"username": str(uuid4()), "password": "private-secret", "displayName": "User"} | changes
    response = client.post("/api/auth/register", json=body)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert body["password"] not in response.text


def test_draft_lifecycle_and_no_history(api, actors):
    client, session = api
    owner, approver, stranger = actors
    payload = draft_payload(actors)
    response = client.post("/api/requests", headers=owner[1], json=payload)
    assert response.status_code == 201, response.text
    draft = response.json()
    assert draft["applicantId"] == owner[0]["id"]
    assert (draft["status"], draft["currentStep"], draft["version"]) == ("Draft", None, 1)
    assert draft["submittedAt"] is None
    path = "/api/requests/" + draft["id"]
    assert client.get(path, headers=approver[1]).status_code == 200
    assert client.get(path, headers=stranger[1]).status_code == 403
    for actor in (approver, stranger):
        assert client.put(path, headers=actor[1], json=payload | {"version": 1}).status_code == 403
        assert client.delete(path, headers=actor[1]).status_code == 403
    edited = client.put(path, headers=owner[1], json=payload | {"title": "更新标题", "version": 1})
    assert edited.status_code == 200, edited.text
    assert edited.json()["version"] == 2
    assert client.put(path, headers=owner[1], json=payload | {"version": 1}).status_code == 409
    same = client.put(path, headers=owner[1], json=payload | {"title": "更新标题", "version": 2})
    assert same.status_code == 200 and same.json()["version"] == 3
    assert (
        session.scalar(
            select(func.count())
            .select_from(ApprovalHistory)
            .where(ApprovalHistory.request_id == draft["id"])
        )
        == 0
    )
    assert client.delete(path, headers=owner[1]).status_code == 204
    assert client.get(path, headers=owner[1]).status_code == 404
    session.expire_all()
    assert session.get(Request, draft["id"]) is None


@pytest.mark.parametrize(
    "changes",
    [
        {"applicantId": str(uuid4())},
        {"applicant_id": str(uuid4())},
        {"operatorId": str(uuid4())},
        {"status": "Approved"},
        {"currentStep": "Second"},
        {"version": 99},
        {"title": "   "},
        {"title": "x" * 101},
        {"content": " "},
        {"content": "x" * 2001},
        {"firstApproverId": "invalid-uuid"},
    ],
)
def test_invalid_or_forged_create_rejected(api, actors, changes):
    client, session = api
    response = client.post(
        "/api/requests", headers=actors[0][1], json=draft_payload(actors) | changes
    )
    assert response.status_code == 422
    assert (
        session.scalar(
            select(func.count())
            .select_from(Request)
            .where(Request.applicant_id == actors[0][0]["id"])
        )
        == 0
    )


def test_approver_validation_and_rollback(api, actors):
    client, session = api
    for field in ("firstApproverId", "secondApproverId"):
        for value in (actors[0][0]["id"], str(uuid4())):
            response = client.post(
                "/api/requests", headers=actors[0][1], json=draft_payload(actors) | {field: value}
            )
            assert response.status_code == 400
            assert response.json()["error"]["code"] == "INVALID_APPROVER"
    response = client.post("/api/requests", headers=actors[0][1], json=draft_payload(actors))
    assert response.status_code == 201
    path = "/api/requests/" + response.json()["id"]
    bad = client.put(
        path,
        headers=actors[0][1],
        json=draft_payload(actors)
        | {"version": 1, "title": "should not persist", "secondApproverId": str(uuid4())},
    )
    assert bad.status_code == 400
    session.expire_all()
    row = session.get(Request, response.json()["id"])
    assert row.title == "采购申请" and row.version == 1


@pytest.mark.parametrize(
    ("status", "step"), [("InProgress", "First"), ("Approved", None), ("Rejected", None)]
)
def test_non_draft_cannot_be_changed(api, actors, status, step):
    client, session = api
    response = client.post("/api/requests", headers=actors[0][1], json=draft_payload(actors))
    request_id = response.json()["id"]
    session.execute(
        update(Request).where(Request.id == request_id).values(status=status, current_step=step)
    )
    session.commit()
    path = "/api/requests/" + request_id
    assert (
        client.put(
            path, headers=actors[0][1], json=draft_payload(actors) | {"version": 1}
        ).status_code
        == 409
    )
    assert client.delete(path, headers=actors[0][1]).status_code == 409
    session.expire_all()
    assert session.get(Request, request_id).status == status


def test_mine_pagination_filters_and_user_directory(api, actors):
    client, _ = api
    for title in ("A%literal", "ABC", "A%literal second"):
        assert (
            client.post(
                "/api/requests", headers=actors[0][1], json=draft_payload(actors) | {"title": title}
            ).status_code
            == 201
        )
    result = client.get(
        "/api/requests",
        headers=actors[0][1],
        params={"pageSize": 1, "page": 2, "keyword": "%", "status": "Draft"},
    ).json()
    assert result["total"] == 2 and len(result["items"]) == 1 and result["pageSize"] == 1
    assert client.get("/api/requests", headers=actors[1][1]).json()["total"] == 0
    for params in ({"scope": "pending"}, {"page": 0}, {"pageSize": 101}, {"status": "invalid"}):
        assert client.get("/api/requests", headers=actors[0][1], params=params).status_code == 422
    result = client.get(
        "/api/users", headers=actors[0][1], params={"keyword": actors[1][0]["username"]}
    )
    assert result.status_code == 200
    assert result.json()["total"] == 1
    assert set(result.json()["items"][0]) == {"id", "username", "displayName"}
    assert client.get("/api/requests/not-a-uuid", headers=actors[0][1]).status_code == 422
    assert client.get("/api/requests/" + str(uuid4()), headers=actors[0][1]).status_code == 404
