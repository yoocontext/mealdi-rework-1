from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreatePostRq(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    content: str = Field(min_length=1, max_length=5000)


class UpdatePostRq(CreatePostRq):
    pass


class PostRp(BaseModel):
    id: int
    author_id: int
    author_name: str
    content: str
    likes_count: int
    created_at: datetime


class PostListRp(BaseModel):
    items: list[PostRp]


class ToggleLikeRp(BaseModel):
    liked: bool
    likes_count: int
