from dataclasses import dataclass

from application.common.exceptions import PostNotFoundError
from application.common.use_case import BaseUseCase
from application.dto.posts import Post
from application.interfaces.dm.likes import ILikeDm
from application.interfaces.dm.posts import IPostDm
from application.interfaces.transaction import ITransactionManager


@dataclass(kw_only=True, frozen=True, slots=True)
class TogglePostLikeCm:
    post_id: int
    user_id: int


@dataclass(kw_only=True, frozen=True, slots=True)
class TogglePostLikeRs:
    liked: bool
    likes_count: int


@dataclass(kw_only=True, slots=True)
class TogglePostLikeUc(BaseUseCase[TogglePostLikeCm, TogglePostLikeRs]):
    """Toggle a unique like without a denormalized counter.

    Pipeline:
    1. Verify the post exists and load the caller's like.
    2. Create or delete the unique like row.
    3. Commit, derive the new count, and return state.
    """

    _posts: IPostDm
    _likes: ILikeDm
    _transaction: ITransactionManager

    async def act(self, *, command: TogglePostLikeCm) -> TogglePostLikeRs:
        liked = await self._toggle(
            user_id=command.user_id,
            post_id=command.post_id,
        )

        await self._transaction.commit()

        post = await self._require_post(post_id=command.post_id)

        return TogglePostLikeRs(liked=liked, likes_count=post.likes_count)

    async def _toggle(self, *, user_id: int, post_id: int) -> bool:
        if not await self._likes.lock_post(post_id=post_id):
            raise PostNotFoundError()

        was_liked = await self._likes.exists(user_id=user_id, post_id=post_id)

        if was_liked:
            await self._likes.delete(user_id=user_id, post_id=post_id)
        else:
            await self._likes.create(user_id=user_id, post_id=post_id)

        return not was_liked

    async def _require_post(self, *, post_id: int) -> Post:
        post = await self._posts.get_by_id(post_id=post_id)
        if post is None:
            raise PostNotFoundError()

        return post
