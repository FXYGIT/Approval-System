from typing import Literal
from uuid import UUID

from app.schemas.common import APIModel, UTCTime
from app.schemas.request import Status, Step
from app.schemas.user import UserSummary

Action = Literal["Submit", "FirstApprove", "FirstReject", "SecondApprove", "SecondReject"]


class HistoryEntry(APIModel):
    id: UUID
    action: Action
    operator: UserSummary
    step: Step | None
    comment: str | None
    previous_status: Status | None
    previous_step: Step | None
    new_status: Status
    new_step: Step | None
    created_at: UTCTime
