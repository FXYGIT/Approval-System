from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Query, Response

from app.api.deps import CurrentUser, DBSession
from app.schemas.common import ERROR_RESPONSES, Page
from app.schemas.request import DraftInput, DraftUpdate, RequestPublic, Status
from app.services import requests

router = APIRouter(prefix="/api/requests", tags=["requests"], responses=ERROR_RESPONSES)


@router.post("", response_model=RequestPublic, status_code=201, summary="创建申请草稿")
def create(data: DraftInput, session: DBSession, user: CurrentUser):
    return requests.create(session, user.id, data)


@router.get("", response_model=Page[RequestPublic], summary="查询我发起的申请")
def list_mine(
    session: DBSession,
    user: CurrentUser,
    scope: Literal["mine"] = "mine",
    page: Annotated[int, Query(ge=1, le=1000000)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 10,
    status: Status | None = None,
    keyword: Annotated[str, Query(max_length=100)] = "",
):
    return requests.list_mine(session, user.id, page, page_size, status, keyword.strip())


@router.get("/{request_id}", response_model=RequestPublic, summary="查看申请详情")
def detail(request_id: UUID, session: DBSession, user: CurrentUser):
    return requests.detail(session, user.id, str(request_id))


@router.put("/{request_id}", response_model=RequestPublic, summary="编辑自己的申请草稿")
def edit(request_id: UUID, data: DraftUpdate, session: DBSession, user: CurrentUser):
    return requests.edit(session, user.id, str(request_id), data)


@router.delete("/{request_id}", status_code=204, summary="删除自己的申请草稿")
def delete(request_id: UUID, session: DBSession, user: CurrentUser):
    requests.delete(session, user.id, str(request_id))
    return Response(status_code=204)
