from fastapi import APIRouter

from app.api.deps import DBSession
from app.schemas.common import ERROR_RESPONSES
from app.schemas.user import LoginInput, RegisterInput, TokenResponse, UserPublic
from app.services import users

router = APIRouter(prefix="/api/auth", tags=["auth"], responses=ERROR_RESPONSES)


@router.post("/register", response_model=UserPublic, status_code=201, summary="注册用户")
def register(data: RegisterInput, session: DBSession):
    return users.register(session, data)


@router.post("/login", response_model=TokenResponse, summary="登录并获取访问令牌")
def login(data: LoginInput, session: DBSession):
    return users.login(session, data)
