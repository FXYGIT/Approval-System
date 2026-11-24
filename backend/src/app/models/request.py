from datetime import datetime
from typing import ClassVar

from sqlalchemy import CHAR, CheckConstraint, ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TABLE_OPTIONS, Base, new_id, utc_now
from app.models.user import User


class Request(Base):
    __tablename__ = "requests"
    __table_args__ = (
        CheckConstraint(
            "(status IN ('Draft', 'Approved', 'Rejected') AND current_step IS NULL) "
            "OR (status = 'InProgress' AND current_step IS NOT NULL "
            "AND current_step IN ('First', 'Second'))",
            name="status_step",
        ),
        CheckConstraint("applicant_id <> first_approver_id", name="first_not_applicant"),
        CheckConstraint("applicant_id <> second_approver_id", name="second_not_applicant"),
        CheckConstraint("version >= 1", name="positive_version"),
        Index("ix_requests_applicant_created", "applicant_id", "created_at", "id"),
        Index(
            "ix_requests_first_pending",
            "first_approver_id",
            "status",
            "current_step",
            "created_at",
            "id",
        ),
        Index(
            "ix_requests_second_pending",
            "second_approver_id",
            "status",
            "current_step",
            "created_at",
            "id",
        ),
        TABLE_OPTIONS,
    )

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=new_id)
    title: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(String(2000))
    status: Mapped[str] = mapped_column(String(20), default="Draft")
    applicant_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("users.id", ondelete="RESTRICT"))
    first_approver_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="RESTRICT")
    )
    second_approver_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="RESTRICT")
    )
    current_step: Mapped[str | None] = mapped_column(String(20))
    version: Mapped[int] = mapped_column(Integer, default=1, server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), default=utc_now, onupdate=utc_now)
    submitted_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6))
    applicant: Mapped[User] = relationship(foreign_keys=[applicant_id])
    first_approver: Mapped[User] = relationship(foreign_keys=[first_approver_id])
    second_approver: Mapped[User] = relationship(foreign_keys=[second_approver_id])
    __mapper_args__: ClassVar[dict] = {"version_id_col": version}
