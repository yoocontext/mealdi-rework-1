from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infra.common.orm import Base

if TYPE_CHECKING:
    from infra.orm.users import UserOrm


class MessageOrm(Base):
    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint("sender_id <> recipient_id", name="different_users"),
        CheckConstraint("length(content) BETWEEN 1 AND 4000", name="content_len"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    sender: Mapped["UserOrm"] = relationship(
        back_populates="sent_messages",
        foreign_keys="MessageOrm.sender_id",
    )
    recipient: Mapped["UserOrm"] = relationship(
        back_populates="received_messages",
        foreign_keys="MessageOrm.recipient_id",
    )

    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )

    content: Mapped[str] = mapped_column(String(4000))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )
