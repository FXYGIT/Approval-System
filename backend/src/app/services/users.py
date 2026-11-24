from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.repositories import users
from app.schemas.common import Page
from app.schemas.user import LoginInput, RegisterInput, TokenResponse, UserPublic, UserSummary
from app.services.transactions import transaction


def register(session: Session, data: RegisterInput) -> UserPublic:
    try:
        with transaction(session):
            if users.by_username(session, data.username):
                raise BusinessError(409, "USERNAME_ALREADY_EXISTS", "用户名已存在")
            user = users.add(
                session,
                User(
                    username=data.username,
                    display_name=data.display_name,
                    password_hash=hash_password(data.password),
                ),
            )
            result = UserPublic.model_validate(user)
        return result
    except IntegrityError as exc:
        if exc.orig.args[0] == 1062:
            raise BusinessError(409, "USERNAME_ALREADY_EXISTS", "用户名已存在") from None
        raise


def login(session: Session, data: LoginInput) -> TokenResponse:
    user = users.by_username(session, data.username)
    if not verify_password(data.password, user.password_hash if user else None):
        raise BusinessError(401, "INVALID_CREDENTIALS", "用户名或密码错误")
    token, expires = create_access_token(user.id)
    return TokenResponse(access_token=token, expires_in=expires)


def authenticated_user(session: Session, user_id: str) -> User:
    user = users.by_id(session, user_id)
    if user is None:
        raise BusinessError(401, "INVALID_TOKEN", "身份凭证无效或已过期")
    return user


def list_users(session: Session, page: int, page_size: int, keyword: str) -> Page[UserSummary]:
    rows, total = users.list_users(session, page, page_size, keyword)
    return Page[UserSummary](items=rows, total=total, page=page, page_size=page_size)
