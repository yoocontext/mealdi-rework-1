from dataclasses import dataclass

from application.common.use_case import BaseUseCase
from application.dto.posts import Post
from application.interfaces.dm.posts import IPostDm
from application.interfaces.transaction import ITransactionManager


@dataclass(kw_only=True, frozen=True, slots=True)
class CreatePostCm:
    author_id: int
    content: str


@dataclass(kw_only=True, frozen=True, slots=True)
class CreatePostRs:
    post: Post


@dataclass(kw_only=True, slots=True)
class CreatePostUc(BaseUseCase[CreatePostCm, CreatePostRs]):
    """Create a post owned by the authenticated user.

    Pipeline:
    1. Normalize content.
    2. Persist the post.
    3. Commit and return it.

    Edge cases:
    - Transport validation guarantees non-empty bounded content.
    """

    _posts: IPostDm
    _transaction: ITransactionManager

    async def act(self, *, command: CreatePostCm) -> CreatePostRs:
        # Normalize and persist content under the authenticated author.
        post = await self._posts.create(
            author_id=command.author_id,
            content=command.content.strip(),
        )

        # Return the post only after it becomes durable.
        await self._transaction.commit()
        return CreatePostRs(post=post)
