from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import User


def by_username(session: Session, username: str) -> User | None:
    return session.scalar(select(User).where(User.username == username))


def by_id(session: Session, user_id: str) -> User | None:
    return session.get(User, user_id)


def add(session: Session, user: User) -> User:
    session.add(user)
    session.flush()
    return user


def list_users(session: Session, page: int, page_size: int, keyword: str):
    filters = [User.username.contains(keyword, autoescape=True)] if keyword else []
    total = session.scalar(select(func.count()).select_from(User).where(*filters))
    rows = session.scalars(
        select(User)
        .where(*filters)
        .order_by(User.username, User.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return rows, total
