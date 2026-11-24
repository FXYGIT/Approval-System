from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError
from app.models import Request
from app.repositories import requests, users
from app.schemas.common import Page
from app.schemas.request import DraftInput, DraftUpdate, RequestPublic
from app.services.transactions import transaction


def get_request(session: Session, request_id: str) -> Request:
    row = requests.by_id(session, request_id)
    if row is None:
        raise BusinessError(404, "REQUEST_NOT_FOUND", "申请不存在")
    return row


def require_owner_draft(row: Request, user_id: str):
    if row.applicant_id != user_id:
        raise BusinessError(403, "REQUEST_FORBIDDEN", "只有申请人可以修改草稿")
    if row.status != "Draft":
        raise BusinessError(409, "INVALID_REQUEST_STATE", "只有草稿可以修改或删除")


def validate_approvers(session: Session, user_id: str, data: DraftInput):
    for approver_id in {str(data.first_approver_id), str(data.second_approver_id)}:
        if approver_id == user_id or users.by_id(session, approver_id) is None:
            raise BusinessError(400, "INVALID_APPROVER", "审批人必须存在且不能是申请人本人")


def draft_values(data: DraftInput) -> dict:
    return {
        "title": data.title,
        "content": data.content,
        "first_approver_id": str(data.first_approver_id),
        "second_approver_id": str(data.second_approver_id),
    }


def create(session: Session, user_id: str, data: DraftInput) -> RequestPublic:
    with transaction(session):
        validate_approvers(session, user_id, data)
        row = requests.add(session, Request(applicant_id=user_id, **draft_values(data)))
        result = RequestPublic.model_validate(row)
    return result


def detail(session: Session, user_id: str, request_id: str) -> RequestPublic:
    row = get_request(session, request_id)
    if user_id not in (row.applicant_id, row.first_approver_id, row.second_approver_id):
        raise BusinessError(403, "REQUEST_FORBIDDEN", "无权查看该申请")
    return RequestPublic.model_validate(row)


def list_mine(
    session: Session, user_id: str, page: int, page_size: int, status: str | None, keyword: str
) -> Page[RequestPublic]:
    rows, total = requests.list_mine(session, user_id, page, page_size, status, keyword)
    return Page[RequestPublic](items=rows, total=total, page=page, page_size=page_size)


def edit(session: Session, user_id: str, request_id: str, data: DraftUpdate) -> RequestPublic:
    with transaction(session):
        row = get_request(session, request_id)
        require_owner_draft(row, user_id)
        if row.version != data.version:
            raise BusinessError(409, "REQUEST_CONFLICT", "申请已发生变化，请刷新后重试")
        validate_approvers(session, user_id, data)
        if requests.update_draft(session, row, data.version, draft_values(data)) != 1:
            raise BusinessError(409, "REQUEST_CONFLICT", "申请已发生变化，请刷新后重试")
        result = RequestPublic.model_validate(requests.by_id(session, request_id))
    return result


def delete(session: Session, user_id: str, request_id: str):
    with transaction(session):
        row = get_request(session, request_id)
        require_owner_draft(row, user_id)
        if requests.delete_draft(session, row) != 1:
            raise BusinessError(409, "REQUEST_CONFLICT", "申请已发生变化，请刷新后重试")
