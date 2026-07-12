from datetime import datetime
from typing import ClassVar
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Uuid, func
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


class IntegerIdMixin:
    id: Mapped[int] = mapped_column(primary_key=True)


class UuidIdMixin:
    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        default=uuid4,
        primary_key=True,
    )


class CreatedAtMixin:
    _created_at_index: ClassVar[bool] = False

    @declared_attr
    def created_at(self) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
            index=self._created_at_index,
        )


class UpdatedAtMixin:
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
