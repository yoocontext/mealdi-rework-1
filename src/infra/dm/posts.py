from dataclasses import dataclass

from sqlalchemy import Select, func, select

from application.dto.posts import Post
from application.interfaces.dm.posts import IPostDm
from infra.common.transaction import TransactionManager
from infra.dm.exceptions import SerializationError
from infra.dm.mappers.posts import map_post
from infra.orm.likes import LikeOrm
from infra.orm.posts import PostOrm
from infra.orm.users import UserOrm


def _post_query() -> Select[tuple[PostOrm, str, int]]:
    return (
        select(PostOrm, UserOrm.name, func.count(LikeOrm.user_id))
        .join(UserOrm, UserOrm.id == PostOrm.author_id)
        .outerjoin(LikeOrm, LikeOrm.post_id == PostOrm.id)
        .group_by(PostOrm.id, UserOrm.name)
    )


@dataclass(kw_only=True, slots=True)
class PostDm(IPostDm):
    _tm: TransactionManager

    async def get_by_id(
        self,
        *,
        post_id: int,
        for_update: bool = False,
    ) -> Post | None:
        if for_update:
            lock = select(PostOrm.id).where(PostOrm.id == post_id).with_for_update()
            if await self._tm.scalar(statement=lock) is None:
                return None

        row = (
            await self._tm.execute(
                statement=_post_query().where(PostOrm.id == post_id),
            )
        ).one_or_none()
        if row is None:
            return None

        return map_post(
            orm=row[0],
            author_name=row[1],
            likes_count=row[2],
        )

    async def list(
        self,
        *,
        author_id: int | None = None,
        content_query: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Post, ...]:
        query = _post_query()
        if author_id is not None:
            query = query.where(PostOrm.author_id == author_id)
        if content_query is not None:
            escaped = content_query.replace("%", "\\%").replace("_", "\\_")
            query = query.where(PostOrm.content.ilike(f"%{escaped}%", escape="\\"))

        rows = (
            await self._tm.execute(
                statement=query.order_by(PostOrm.created_at.desc(), PostOrm.id.desc())
                .limit(limit)
                .offset(offset),
            )
        ).all()
        return tuple(
            map_post(
                orm=orm,
                author_name=author_name,
                likes_count=likes_count,
            )
            for orm, author_name, likes_count in rows
        )

    async def create(self, *, author_id: int, content: str) -> Post:
        orm = PostOrm(author_id=author_id, content=content)

        self._tm.add(instance=orm)
        await self._tm.flush(instances=[orm])

        return await self._reload(post_id=orm.id, operation="create")

    async def save(self, *, post: Post) -> Post:
        orm = await self._tm.get(entity=PostOrm, identifier=post.id)
        if orm is None:
            raise SerializationError(
                entity="post",
                identifier=post.id,
                operation="save",
            )

        orm.content = post.content
        await self._tm.flush(instances=[orm])

        return await self._reload(post_id=orm.id, operation="save")

    async def delete(self, *, post_id: int) -> None:
        orm = await self._tm.get(entity=PostOrm, identifier=post_id)
        if orm is None:
            return

        await self._tm.delete(instance=orm)
        await self._tm.flush()

    async def _reload(self, *, post_id: int, operation: str) -> Post:
        post = await self.get_by_id(post_id=post_id)
        if post is not None:
            return post

        raise SerializationError(
            entity="post",
            identifier=post_id,
            operation=operation,
        )
