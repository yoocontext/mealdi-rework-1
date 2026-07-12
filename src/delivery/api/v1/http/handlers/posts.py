from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Query, Response, status

from application.use_cases.posts import (
    CreatePostCm,
    CreatePostUc,
    DeletePostCm,
    DeletePostUc,
    ListPostsCm,
    ListPostsUc,
    TogglePostLikeCm,
    TogglePostLikeUc,
    UpdatePostCm,
    UpdatePostUc,
)
from delivery.api.v1.http.dependencies import CurrentUser
from delivery.api.v1.http.mappers.posts import map_post_to_rp, map_posts_to_rp
from delivery.api.v1.http.schemas.posts import (
    CreatePostRq,
    PostListRp,
    PostRp,
    ToggleLikeRp,
    UpdatePostRq,
)

router = APIRouter(prefix="/api/v1/http/posts", tags=["posts"])


@router.get("", response_model=PostListRp)
@inject
async def list_posts(
    *,
    use_case: FromDishka[ListPostsUc],
    author_id: int | None = Query(default=None, gt=0),
    q: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PostListRp:
    result = await use_case.act(
        command=ListPostsCm(
            author_id=author_id,
            content_query=q,
            limit=limit,
            offset=offset,
        ),
    )

    return map_posts_to_rp(posts=result.posts)


@router.post("", response_model=PostRp, status_code=status.HTTP_201_CREATED)
@inject
async def create_post(
    *,
    request: CreatePostRq,
    current_user: CurrentUser,
    use_case: FromDishka[CreatePostUc],
) -> PostRp:
    result = await use_case.act(
        command=CreatePostCm(author_id=current_user.id, content=request.content),
    )

    return map_post_to_rp(post=result.post)


@router.put("/{post_id}", response_model=PostRp)
@inject
async def update_post(
    *,
    post_id: int,
    request: UpdatePostRq,
    current_user: CurrentUser,
    use_case: FromDishka[UpdatePostUc],
) -> PostRp:
    result = await use_case.act(
        command=UpdatePostCm(
            post_id=post_id,
            actor_id=current_user.id,
            content=request.content,
        ),
    )

    return map_post_to_rp(post=result.post)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_post(
    *,
    post_id: int,
    current_user: CurrentUser,
    use_case: FromDishka[DeletePostUc],
) -> Response:
    await use_case.act(
        command=DeletePostCm(post_id=post_id, actor_id=current_user.id),
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{post_id}/likes/toggle", response_model=ToggleLikeRp)
@inject
async def toggle_post_like(
    *,
    post_id: int,
    current_user: CurrentUser,
    use_case: FromDishka[TogglePostLikeUc],
) -> ToggleLikeRp:
    result = await use_case.act(
        command=TogglePostLikeCm(post_id=post_id, user_id=current_user.id),
    )

    return ToggleLikeRp(liked=result.liked, likes_count=result.likes_count)
