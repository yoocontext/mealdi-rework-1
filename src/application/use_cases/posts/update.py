from dataclasses import dataclass, replace

from application.common.exceptions import PostNotFoundError, PostOwnershipError
from application.common.use_case import BaseUseCase
from application.dto.posts import Post
from application.interfaces.dm.posts import IPostDm
from application.interfaces.transaction import ITransactionManager


@dataclass(kw_only=True, frozen=True, slots=True)
class UpdatePostCm:
    post_id: int
    actor_id: int
    content: str


@dataclass(kw_only=True, frozen=True, slots=True)
class UpdatePostRs:
    post: Post


@dataclass(kw_only=True, slots=True)
class UpdatePostUc(BaseUseCase[UpdatePostCm, UpdatePostRs]):
    """Edit an owned post.

    Pipeline:
    1. Load the post and verify ownership.
    2. Persist normalized replacement content.
    3. Commit and return the updated post.

    Edge cases:
    - Missing posts and edits by non-owners are distinct failures.
    """

    _posts: IPostDm
    _transaction: ITransactionManager

    async def act(self, *, command: UpdatePostCm) -> UpdatePostRs:
        post = await self._get_owned_post(
            post_id=command.post_id,
            actor_id=command.actor_id,
        )

        updated = await self._posts.save(
            post=replace(post, content=command.content.strip()),
        )
        await self._transaction.commit()

        return UpdatePostRs(post=updated)

    async def _get_owned_post(self, *, post_id: int, actor_id: int) -> Post:
        post = await self._posts.get_by_id(post_id=post_id, for_update=True)
        if post is None:
            raise PostNotFoundError()
        if post.author_id != actor_id:
            raise PostOwnershipError(action="edit")

        return post
