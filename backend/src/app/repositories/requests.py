from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session, joinedload

from app.db.base import utc_now
from app.models import Request


def query():
    return select(Request).options(
        joinedload(Request.applicant),
        joinedload(Request.first_approver),
        joinedload(Request.second_approver),
    )


def by_id(session: Session, request_id: str) -> Request | None:
    return session.scalar(
        query().where(Request.id == request_id).execution_options(populate_existing=True)
    )


def add(session: Session, row: Request) -> Request:
    session.add(row)
    session.flush()
    return by_id(session, row.id)


def list_mine(
    session: Session, user_id: str, page: int, page_size: int, status: str | None, keyword: str
):
    filters = [Request.applicant_id == user_id]
    if status:
        filters.append(Request.status == status)
    if keyword:
        filters.append(Request.title.contains(keyword, autoescape=True))
    total = session.scalar(select(func.count()).select_from(Request).where(*filters))
    rows = session.scalars(
        query()
        .where(*filters)
        .order_by(Request.created_at.desc(), Request.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return rows, total


def update_draft(session: Session, row: Request, version: int, values: dict) -> int:
    result = session.execute(
        update(Request)
        .where(
            Request.id == row.id,
            Request.applicant_id == row.applicant_id,
            Request.status == "Draft",
            Request.version == version,
        )
        .values(**values, version=Request.version + 1, updated_at=utc_now())
        .execution_options(synchronize_session=False)
    )
    return result.rowcount


def delete_draft(session: Session, row: Request) -> int:
    result = session.execute(
        delete(Request)
        .where(
            Request.id == row.id,
            Request.applicant_id == row.applicant_id,
            Request.status == "Draft",
            Request.version == row.version,
        )
        .execution_options(synchronize_session=False)
    )
    return result.rowcount
