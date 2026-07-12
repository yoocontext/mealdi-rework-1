from application.dto.posts import Post
from delivery.api.v1.http.schemas.posts import PostListRp, PostRp


def map_post_to_rp(*, post: Post) -> PostRp:
    return PostRp(
        id=post.id,
        author_id=post.author_id,
        author_name=post.author_name,
        content=post.content,
        likes_count=post.likes_count,
        created_at=post.created_at,
    )


def map_posts_to_rp(*, posts: tuple[Post, ...]) -> PostListRp:
    return PostListRp(items=[map_post_to_rp(post=post) for post in posts])
