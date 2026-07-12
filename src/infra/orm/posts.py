from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infra.orm.common import Base, CreatedAtMixin, IntegerIdMixin

if TYPE_CHECKING:
    from infra.orm.likes import LikeOrm
    from infra.orm.users import UserOrm


class PostOrm(IntegerIdMixin, CreatedAtMixin, Base):
    __tablename__ = "posts"
    _created_at_index = True
    __table_args__ = (
        CheckConstraint("length(content) BETWEEN 1 AND 5000", name="content_len"),
    )

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
