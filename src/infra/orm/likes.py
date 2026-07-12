from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infra.common.orm import Base

if TYPE_CHECKING:
    from infra.orm.posts import PostOrm
    from infra.orm.users import UserOrm


class LikeOrm(Base):
    __tablename__ = "likes"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    post_id: Mapped[int] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"),
        primary_key=True,
    )

    user: Mapped["UserOrm"] = relationship(back_populates="likes")
    post: Mapped["PostOrm"] = relationship(back_populates="likes")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
