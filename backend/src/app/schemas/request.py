from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, StringConstraints

from app.schemas.common import APIModel, InputModel, UTCTime
from app.schemas.user import UserSummary

Status = Literal["Draft", "InProgress", "Approved", "Rejected"]
Step = Literal["First", "Second"]


class DraftInput(InputModel):
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    content: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
    first_approver_id: UUID
    second_approver_id: UUID


class DraftUpdate(DraftInput):
    version: int = Field(ge=1, strict=True)


class RequestPublic(APIModel):
    id: UUID
    title: str
    content: str
    applicant_id: UUID
    first_approver_id: UUID
    second_approver_id: UUID
    applicant: UserSummary
    first_approver: UserSummary
    second_approver: UserSummary
    status: Status
    current_step: Step | None
    version: int
    created_at: UTCTime
    updated_at: UTCTime
    submitted_at: UTCTime | None
