from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api import auth, requests, users
from app.core.config import auth_settings
from app.core.exceptions import install_exception_handlers
from app.db.session import get_session


@asynccontextmanager
async def lifespan(app: FastAPI):
    auth_settings()
    yield


app = FastAPI(title="Approval System", version="0.2.0", lifespan=lifespan)
install_exception_handlers(app)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(requests.router)


@app.get("/api/health", tags=["health"], summary="检查 API 与数据库连接")
def health(session: Annotated[Session, Depends(get_session)]) -> dict[str, str]:
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Database unavailable") from None
    return {"status": "ok", "database": "ok"}
