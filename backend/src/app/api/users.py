from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DBSession
from app.schemas.common import ERROR_RESPONSES, Page
from app.schemas.user import UserPublic, UserSummary
from app.services import users

router = APIRouter(prefix="/api/users", tags=["users"], responses=ERROR_RESPONSES)


@router.get("/me", response_model=UserPublic, summary="查询当前用户")
def me(user: CurrentUser):
    return user


@router.get("", response_model=Page[UserSummary], summary="分页查询审批人候选用户")
def list_users(
    session: DBSession,
    user: CurrentUser,
    page: Annotated[int, Query(ge=1, le=1000000)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 10,
    keyword: Annotated[str, Query(max_length=50)] = "",
):
    return users.list_users(session, page, page_size, keyword.strip())
