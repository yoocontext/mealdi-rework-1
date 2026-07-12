from dataclasses import dataclass

from application.common.use_case import BaseUseCase
from application.dto.posts import Post
from application.interfaces.dm.posts import IPostDm


@dataclass(kw_only=True, frozen=True, slots=True)
class ListPostsCm:
    author_id: int | None = None
    content_query: str | None = None
    limit: int = 50
    offset: int = 0


@dataclass(kw_only=True, frozen=True, slots=True)
class ListPostsRs:
    posts: tuple[Post, ...]


@dataclass(kw_only=True, slots=True)
class ListPostsUc(BaseUseCase[ListPostsCm, ListPostsRs]):
    """List or search the feed.

    Pipeline:
    1. Normalize the optional text query.
    2. Query a bounded page newest-first.
    3. Return posts or an empty result.
    """

    _posts: IPostDm

    async def act(self, *, command: ListPostsCm) -> ListPostsRs:
        # Normalize optional search text into an explicit absent-or-value filter.
        content_query = command.content_query
        if content_query is not None:
            content_query = content_query.strip() or None

        # Keep pagination bounded before delegating the read projection.
        posts = await self._posts.list(
            author_id=command.author_id,
            content_query=content_query,
            limit=min(max(command.limit, 1), 100),
            offset=max(command.offset, 0),
        )
        return ListPostsRs(posts=posts)
