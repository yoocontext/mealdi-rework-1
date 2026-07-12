from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterUserRq(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    name: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=10, max_length=128)


class PublicUserRp(BaseModel):
    id: int
    name: str
    created_at: datetime


class CurrentUserRp(PublicUserRp):
    email: EmailStr
