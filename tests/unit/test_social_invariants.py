from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from application.common.exceptions import (
    PostNotFoundError,
    PostOwnershipError,
    SelfMessagingError,
    UserNotFoundError,
)
from application.dto.posts import Post
from application.use_cases.messages.send import SendMessageCm, SendMessageUc
from application.use_cases.posts.delete import DeletePostCm, DeletePostUc
from application.use_cases.posts.list import ListPostsCm, ListPostsUc
from application.use_cases.posts.toggle_like import (
    TogglePostLikeCm,
    TogglePostLikeUc,
)
from application.use_cases.posts.update import UpdatePostCm, UpdatePostUc

POST = Post(
    id=13,
    author_id=7,
    author_name="Alice",
    content="original",
    likes_count=0,
    created_at=datetime(2026, 7, 12, 10, tzinfo=UTC),
)


async def test_non_author_cannot_update_or_delete_post() -> None:
    posts = AsyncMock()
    posts.get_by_id.return_value = POST
    transaction = AsyncMock()
    update = UpdatePostUc(_posts=posts, _transaction=transaction)
    delete = DeletePostUc(_posts=posts, _transaction=transaction)

    with pytest.raises(PostOwnershipError):
        await update.act(
            command=UpdatePostCm(post_id=POST.id, actor_id=99, content="stolen"),
        )
    with pytest.raises(PostOwnershipError):
        await delete.act(
            command=DeletePostCm(post_id=POST.id, actor_id=99),
        )

    assert posts.get_by_id.await_count == 2
    assert all(call.kwargs["for_update"] for call in posts.get_by_id.await_args_list)
    posts.save.assert_not_awaited()
    posts.delete.assert_not_awaited()
    transaction.commit.assert_not_awaited()


async def test_feed_filters_are_normalized_and_bounded_before_query() -> None:
    posts = AsyncMock()
    posts.list.return_value = ()
    use_case = ListPostsUc(_posts=posts)

    await use_case.act(
        command=ListPostsCm(
            author_id=7,
            content_query="   ",
            limit=10_000,
            offset=-10,
        ),
    )

    posts.list.assert_awaited_once_with(
        author_id=7,
        content_query=None,
        limit=100,
        offset=0,
    )


async def test_like_toggle_requires_locked_existing_post() -> None:
    posts = AsyncMock()
    likes = AsyncMock()
    likes.lock_post.return_value = False
    transaction = AsyncMock()
    use_case = TogglePostLikeUc(
        _posts=posts,
        _likes=likes,
        _transaction=transaction,
    )

    with pytest.raises(PostNotFoundError):
        await use_case.act(
            command=TogglePostLikeCm(post_id=404, user_id=7),
        )

    likes.exists.assert_not_awaited()
    likes.create.assert_not_awaited()
    likes.delete.assert_not_awaited()
    transaction.commit.assert_not_awaited()


@pytest.mark.parametrize(
    ("sender_id", "recipient_id", "error"),
    [
        (7, 7, SelfMessagingError),
        (7, 404, UserNotFoundError),
    ],
)
async def test_invalid_message_recipient_cannot_create_message(
    *,
    sender_id: int,
    recipient_id: int,
    error: type[Exception],
) -> None:
    users = AsyncMock()
    users.get_by_id.return_value = None
    messages = AsyncMock()
    transaction = AsyncMock()
    use_case = SendMessageUc(
        _messages=messages,
        _users=users,
        _transaction=transaction,
    )

    with pytest.raises(error):
        await use_case.act(
            command=SendMessageCm(
                sender_id=sender_id,
                recipient_id=recipient_id,
                content="private",
            ),
        )

    messages.create.assert_not_awaited()
    transaction.commit.assert_not_awaited()
