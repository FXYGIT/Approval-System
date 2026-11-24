from datetime import datetime

from sqlalchemy import CHAR, String
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import TABLE_OPTIONS, Base, new_id, utc_now


class User(Base):
    __tablename__ = "users"
    __table_args__ = TABLE_OPTIONS

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=new_id)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), default=utc_now)
