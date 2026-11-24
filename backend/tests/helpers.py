from uuid import uuid4


def register(client, name=None):
    payload = {
        "username": name or str(uuid4()),
        "password": " password-123 ",
        "displayName": "测试用户",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201, response.text
    login = client.post("/api/auth/login", json={k: payload[k] for k in ("username", "password")})
    assert login.status_code == 200, login.text
    return response.json(), {"Authorization": "Bearer " + login.json()["accessToken"]}


def draft_payload(actors):
    return {
        "title": "采购申请",
        "content": "采购设备",
        "firstApproverId": actors[1][0]["id"],
        "secondApproverId": actors[1][0]["id"],
    }
