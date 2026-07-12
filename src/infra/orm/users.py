from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infra.orm.common import Base, CreatedAtMixin, IntegerIdMixin

if TYPE_CHECKING:
    from infra.orm.likes import LikeOrm
    from infra.orm.messages import MessageOrm
    from infra.orm.posts import PostOrm
    from infra.orm.refresh_sessions import RefreshSessionOrm


class UserOrm(IntegerIdMixin, CreatedAtMixin, Base):
    __tablename__ = "users"

    posts: Mapped[list["PostOrm"]] = relationship(
        back_populates="author",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    likes: Mapped[list["LikeOrm"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    sent_messages: Mapped[list["MessageOrm"]] = relationship(
        back_populates="sender",
        foreign_keys="MessageOrm.sender_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    received_messages: Mapped[list["MessageOrm"]] = relationship(
        back_populates="recipient",
        foreign_keys="MessageOrm.recipient_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    refresh_sessions: Mapped[list["RefreshSessionOrm"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(50), index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
