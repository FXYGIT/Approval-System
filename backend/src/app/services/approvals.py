from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError
from app.models import ApprovalHistory, Request
from app.repositories import history as history_repo
from app.repositories import requests as requests_repo
from app.schemas.history import HistoryEntry
from app.schemas.request import ApproveInput, RejectInput, RequestPublic
from app.services.requests import get_request
from app.services.transactions import transaction


def _resolve_approval(row: Request, user_id: str) -> str:
    if row.status != "InProgress" or row.current_step not in ("First", "Second"):
        raise BusinessError(409, "INVALID_REQUEST_STATE", "当前申请状态不允许审批")
    step = row.current_step
    assigned = row.first_approver_id if step == "First" else row.second_approver_id
    if assigned != user_id:
        raise BusinessError(403, "APPROVAL_NOT_ASSIGNED", "只有当前节点的审批人可以操作")
    return step


def _check_version(row: Request, version: int | None):
    if version is not None and version != row.version:
        raise BusinessError(409, "APPROVAL_CONFLICT", "申请已发生变化，请刷新后重试")


def _apply(
    session: Session,
    row: Request,
    user_id: str,
    step: str,
    to_status: str,
    to_step: str | None,
    action: str,
    comment: str | None,
) -> RequestPublic:
    if requests_repo.advance_approval(session, row, user_id, step, to_status, to_step) != 1:
        raise BusinessError(409, "APPROVAL_CONFLICT", "申请已发生变化，请刷新后重试")
    history_repo.add(
        session,
        ApprovalHistory(
            request_id=row.id,
            action=action,
            operator_id=user_id,
            step=step,
            comment=comment,
            previous_status="InProgress",
            previous_step=step,
            new_status=to_status,
            new_step=to_step,
        ),
    )
    return RequestPublic.model_validate(requests_repo.by_id(session, row.id))


def submit(session: Session, user_id: str, request_id: str) -> RequestPublic:
    with transaction(session):
        row = get_request(session, request_id)
        if row.applicant_id != user_id:
            raise BusinessError(403, "REQUEST_FORBIDDEN", "只有申请人可以提交申请")
        if row.status != "Draft":
            raise BusinessError(409, "INVALID_REQUEST_STATE", "只有草稿可以提交")
        if requests_repo.submit_draft(session, row, user_id) != 1:
            raise BusinessError(409, "APPROVAL_CONFLICT", "申请已发生变化，请刷新后重试")
        history_repo.add(
            session,
            ApprovalHistory(
                request_id=row.id,
                action="Submit",
                operator_id=user_id,
                step=None,
                comment=None,
                previous_status="Draft",
                previous_step=None,
                new_status="InProgress",
                new_step="First",
            ),
        )
        result = RequestPublic.model_validate(requests_repo.by_id(session, row.id))
    return result


def approve(session: Session, user_id: str, request_id: str, data: ApproveInput) -> RequestPublic:
    with transaction(session):
        row = get_request(session, request_id)
        step = _resolve_approval(row, user_id)
        _check_version(row, data.version)
        if step == "First":
            return _apply(
                session, row, user_id, "First", "InProgress", "Second", "FirstApprove", data.comment
            )
        return _apply(
            session, row, user_id, "Second", "Approved", None, "SecondApprove", data.comment
        )


def reject(session: Session, user_id: str, request_id: str, data: RejectInput) -> RequestPublic:
    with transaction(session):
        row = get_request(session, request_id)
        step = _resolve_approval(row, user_id)
        _check_version(row, data.version)
        action = "FirstReject" if step == "First" else "SecondReject"
        return _apply(session, row, user_id, step, "Rejected", None, action, data.comment)


def history(session: Session, user_id: str, request_id: str) -> list[HistoryEntry]:
    row = get_request(session, request_id)
    if user_id not in (row.applicant_id, row.first_approver_id, row.second_approver_id):
        raise BusinessError(403, "REQUEST_FORBIDDEN", "无权查看该申请的历史")
    return [
        HistoryEntry.model_validate(h) for h in history_repo.list_for_request(session, request_id)
    ]
