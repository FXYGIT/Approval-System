from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import ApprovalHistory


def add(session: Session, history: ApprovalHistory) -> ApprovalHistory:
    session.add(history)
    session.flush()
    return history


def list_for_request(session: Session, request_id: str):
    return session.scalars(
        select(ApprovalHistory)
        .options(joinedload(ApprovalHistory.operator))
        .where(ApprovalHistory.request_id == request_id)
        .order_by(ApprovalHistory.created_at.asc(), ApprovalHistory.id.asc())
    ).all()
