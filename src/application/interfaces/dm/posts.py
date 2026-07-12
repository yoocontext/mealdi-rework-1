from typing import Protocol

from application.dto.posts import Post


class IPostDm(Protocol):
    async def get_by_id(
        self,
        *,
        post_id: int,
        for_update: bool = False,
    ) -> Post | None: ...

    async def list(
        self,
        *,
        author_id: int | None = None,
        content_query: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Post, ...]: ...

    async def create(self, *, author_id: int, content: str) -> Post: ...

    async def save(self, *, post: Post) -> Post: ...

    async def delete(self, *, post_id: int) -> None: ...
