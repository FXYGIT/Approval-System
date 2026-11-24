from datetime import datetime

from sqlalchemy import CHAR, CheckConstraint, ForeignKey, Index, String
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TABLE_OPTIONS, Base, new_id, utc_now
from app.models.request import Request
from app.models.user import User


class ApprovalHistory(Base):
    __tablename__ = "approval_histories"
    __table_args__ = (
        CheckConstraint(
            "action IN ('Submit', 'FirstApprove', 'FirstReject', 'SecondApprove', 'SecondReject')",
            name="action",
        ),
        Index("ix_approval_histories_request_created", "request_id", "created_at", "id"),
        TABLE_OPTIONS,
    )
    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=new_id)
    request_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("requests.id", ondelete="RESTRICT")
    )
    action: Mapped[str] = mapped_column(String(30))
    operator_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("users.id", ondelete="RESTRICT"))
    step: Mapped[str | None] = mapped_column(String(20))
    comment: Mapped[str | None] = mapped_column(String(500))
    previous_status: Mapped[str | None] = mapped_column(String(20))
    previous_step: Mapped[str | None] = mapped_column(String(20))
    new_status: Mapped[str] = mapped_column(String(20))
    new_step: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), default=utc_now)
    request: Mapped[Request] = relationship(foreign_keys=[request_id])
    operator: Mapped[User] = relationship(foreign_keys=[operator_id])
