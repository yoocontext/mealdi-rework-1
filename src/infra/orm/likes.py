from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infra.orm.common import Base, CreatedAtMixin

if TYPE_CHECKING:
    from infra.orm.posts import PostOrm
    from infra.orm.users import UserOrm


class LikeOrm(CreatedAtMixin, Base):
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
