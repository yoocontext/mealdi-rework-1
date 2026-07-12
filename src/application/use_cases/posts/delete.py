from dataclasses import dataclass

from application.common.exceptions import PostNotFoundError, PostOwnershipError
from application.common.use_case import BaseUseCase
from application.dto.posts import Post
from application.interfaces.dm.posts import IPostDm
from application.interfaces.transaction import ITransactionManager


@dataclass(kw_only=True, frozen=True, slots=True)
class DeletePostCm:
    post_id: int
    actor_id: int


@dataclass(kw_only=True, frozen=True, slots=True)
class DeletePostRs:
    deleted: bool


@dataclass(kw_only=True, slots=True)
class DeletePostUc(BaseUseCase[DeletePostCm, DeletePostRs]):
    """Delete an owned post and its likes.

    Pipeline:
    1. Load the post and verify ownership.
    2. Delete it through the data mapper.
    3. Commit and report success.

    Edge cases:
    - Missing posts and deletes by non-owners are distinct failures.
    """

    _posts: IPostDm
    _transaction: ITransactionManager

    async def act(self, *, command: DeletePostCm) -> DeletePostRs:
        post = await self._get_owned_post(
            post_id=command.post_id,
            actor_id=command.actor_id,
        )

        await self._posts.delete(post_id=post.id)
        await self._transaction.commit()

        return DeletePostRs(deleted=True)

    async def _get_owned_post(self, *, post_id: int, actor_id: int) -> Post:
        post = await self._posts.get_by_id(post_id=post_id, for_update=True)
        if post is None:
            raise PostNotFoundError()
        if post.author_id != actor_id:
            raise PostOwnershipError(action="delete")

        return post
