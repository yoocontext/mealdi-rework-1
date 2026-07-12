from dataclasses import dataclass

from sqlalchemy import select

from application.interfaces.dm.likes import ILikeDm
from infra.common.transaction import TransactionManager
from infra.orm.likes import LikeOrm
from infra.orm.posts import PostOrm


@dataclass(kw_only=True, slots=True)
class LikeDm(ILikeDm):
    _tm: TransactionManager

    async def lock_post(self, *, post_id: int) -> bool:
        query = select(PostOrm.id).where(PostOrm.id == post_id).with_for_update()

        return await self._tm.scalar(statement=query) is not None

    async def exists(self, *, user_id: int, post_id: int) -> bool:
        like = await self._tm.get(
            entity=LikeOrm,
            identifier=(user_id, post_id),
        )

        return like is not None

    async def create(self, *, user_id: int, post_id: int) -> None:
        like = LikeOrm(user_id=user_id, post_id=post_id)

        self._tm.add(instance=like)
        await self._tm.flush(instances=[like])

    async def delete(self, *, user_id: int, post_id: int) -> None:
        like = await self._tm.get(
            entity=LikeOrm,
            identifier=(user_id, post_id),
        )
        if like is None:
            return

        await self._tm.delete(instance=like)
        await self._tm.flush()
