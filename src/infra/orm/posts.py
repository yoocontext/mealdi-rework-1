from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infra.common.orm import Base

if TYPE_CHECKING:
    from infra.orm.likes import LikeOrm
    from infra.orm.users import UserOrm


class PostOrm(Base):
    __tablename__ = "posts"
    __table_args__ = (
        CheckConstraint("length(content) BETWEEN 1 AND 5000", name="content_len"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    author: Mapped["UserOrm"] = relationship(back_populates="posts")
    likes: Mapped[list["LikeOrm"]] = relationship(
        back_populates="post",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )

    content: Mapped[str] = mapped_column(String(5000))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )
