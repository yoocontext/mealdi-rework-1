from application.dto.posts import Post
from infra.common.datetime import as_utc
from infra.orm.posts import PostOrm


def map_post(*, orm: PostOrm, author_name: str, likes_count: int) -> Post:
    return Post(
        id=orm.id,
        author_id=orm.author_id,
        author_name=author_name,
        content=orm.content,
        likes_count=likes_count,
        created_at=as_utc(value=orm.created_at),
    )
