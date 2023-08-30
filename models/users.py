import re
from typing import Optional

import pydantic
from beanie import Indexed
from beanie.operators import In
from pydantic.types import SecretStr

from models import BaseDocument


class UserIn(pydantic.BaseModel):
    username: str
    password: SecretStr


class UserUpdate(pydantic.BaseModel):
    username: Optional[str]
    password: Optional[SecretStr]
    avatar: Optional[str]


class User(pydantic.BaseModel):
    username: str
    password: SecretStr
    scopes: list[str] = []
    avatar: Optional[str] = ""
    followers: list["User"] = []
    following: list["User"] = []

    @pydantic.validator("avatar")
    def avatar_must_be_url(cls, v):
        if not v:
            return v
        # Define a regular expression pattern to match URLs
        url_pattern = r'^https?://(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,6}(?:/[^/]*)*(?:\.(?:jpg|jpeg|png|gif))$'
        if "s3.amazonaws.com" not in v and not re.match(url_pattern, v):
            raise ValueError(f"Avatar must be a url. Received: {v}")
        return v


class UserDocument(User, BaseDocument):
    username: Indexed(str, unique=True)
    password: str
    followers: list[str] = []
    following: list[str] = []

    class Settings:
        name = "users"
        indexes = [("id",), ("username",)]


async def get_followers(follower_ids: list[str]):
    followers = await UserDocument.find(In(UserDocument.id, follower_ids),
                                        limit=100).to_list()
    return followers


async def get_following(following_ids: list[str]):
    following = await UserDocument.find(In(UserDocument.id, following_ids),
                                        limit=100).to_list()
    return following


async def find_user(username: str) -> UserDocument:
    found_user = await UserDocument.find_one({"username": username})
    return found_user
