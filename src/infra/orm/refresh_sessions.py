from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infra.orm.common import Base, CreatedAtMixin, IntegerIdMixin

if TYPE_CHECKING:
    from infra.orm.users import UserOrm


class RefreshSessionOrm(IntegerIdMixin, CreatedAtMixin, Base):
    __tablename__ = "refresh_sessions"

    user: Mapped["UserOrm"] = relationship(back_populates="refresh_sessions")

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )

    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
