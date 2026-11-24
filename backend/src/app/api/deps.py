from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError
from app.core.security import decode_access_token
from app.db.session import get_session
from app.models import User
from app.services.users import authenticated_user

DBSession = Annotated[Session, Depends(get_session)]
bearer = HTTPBearer(auto_error=False)


def get_current_user(
    session: DBSession, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]
) -> User:
    if credentials is None:
        raise BusinessError(401, "AUTHENTICATION_REQUIRED", "请先登录")
    return authenticated_user(session, decode_access_token(credentials.credentials))


CurrentUser = Annotated[User, Depends(get_current_user)]
