from sqlalchemy import and_, delete, func, or_, select, update
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


def submit_draft(session: Session, row: Request, user_id: str) -> int:
    now = utc_now()
    result = session.execute(
        update(Request)
        .where(
            Request.id == row.id,
            Request.applicant_id == user_id,
            Request.status == "Draft",
            Request.current_step.is_(None),
            Request.version == row.version,
        )
        .values(
            status="InProgress",
            current_step="First",
            version=Request.version + 1,
            submitted_at=now,
            updated_at=now,
        )
        .execution_options(synchronize_session=False)
    )
    return result.rowcount


def advance_approval(
    session: Session,
    row: Request,
    approver_id: str,
    from_step: str,
    to_status: str,
    to_step: str | None,
) -> int:
    approver_col = Request.first_approver_id if from_step == "First" else Request.second_approver_id
    result = session.execute(
        update(Request)
        .where(
            Request.id == row.id,
            Request.version == row.version,
            Request.status == "InProgress",
            Request.current_step == from_step,
            approver_col == approver_id,
        )
        .values(
            status=to_status,
            current_step=to_step,
            version=Request.version + 1,
            updated_at=utc_now(),
        )
        .execution_options(synchronize_session=False)
    )
    return result.rowcount


def list_pending(session: Session, user_id: str, page: int, page_size: int, keyword: str):
    filters = [
        or_(
            and_(
                Request.status == "InProgress",
                Request.current_step == "First",
                Request.first_approver_id == user_id,
            ),
            and_(
                Request.status == "InProgress",
                Request.current_step == "Second",
                Request.second_approver_id == user_id,
            ),
        )
    ]
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
