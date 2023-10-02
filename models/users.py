import re
from typing import Any, Optional

import pydantic
from beanie import Indexed
from beanie.odm.fields import PydanticObjectId
from beanie.operators import In
from pydantic.types import SecretStr

from models import BaseDocument


class UserOut(pydantic.BaseModel):
    username: str
    avatar: Optional[str]

    @pydantic.validator("avatar")
    def avatar_must_be_url(cls, v):
        if not v:
            return v
        # Define a regular expression pattern to match URLs
        url_pattern = r'^https?://(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,6}(?:/[^/]*)*(?:\.(?:jpg|jpeg|png|gif))$'
        if "s3.amazonaws.com" not in v and not re.match(url_pattern, v):
            raise ValueError(f"Avatar must be a url. Received: {v}")
        return v

    @pydantic.validator("username")
    def username_must_be_valid(cls, v):
        if not re.match(r"^[a-zA-Z0-9_]{3,20}$", v):
            raise ValueError(
                "Username must be between 3 and 20 characters and only contain alphanumeric characters and underscores"
            )
        return v


class UserIn(pydantic.BaseModel):
    username: str
    password: SecretStr


class UserUpdate(pydantic.BaseModel):
    username: Optional[str]
    password: Optional[SecretStr]
    avatar: Optional[str]


class User(UserOut):
    password: SecretStr
    scopes: list[str] = []
    followers: Optional[list["UserOut"]] = None
    following: Optional[list["UserOut"]] = None

    class Config:
        json_encoders = {
            PydanticObjectId: str
        }  # This line specifies how to serialize ObjectId
        extra = "ignore"  # Ignore fields not defined in the model

    def json(self, *args, **kwargs):
        return super().json(*args, **kwargs, exclude={"password", "scopes"})


class UserDocument(User, BaseDocument):
    username: Indexed(str, unique=True)
    password: str
    followers: list[str] = []
    following: list[str] = []

    class Settings:
        name = "users"
        indexes = [("id",), ("username",)]


async def get_followers(follower_ids: list[str]):
    if not follower_ids:
        return []
    followers = await UserDocument.find(In(UserDocument.username, follower_ids),
                                        limit=100).to_list()
    return followers


async def get_following(following_ids: list[str]):
    if not following_ids:
        return []
    following = await UserDocument.find(In(UserDocument.username,
                                           following_ids),
                                        limit=100).to_list()
    return following


async def generate_user_dict(user: UserDocument) -> dict[str, Any]:
    return {
        **user.dict(),
        "followers": [
            UserOut(**user.dict()).dict()
            for user in await get_followers(user.followers)
        ],
        "following": [
            UserOut(**user.dict()).dict()
            for user in await get_following(user.following)
        ],
    }


async def find_user(username: str) -> UserDocument:
    found_user = await UserDocument.find_one({"username": username})
    return found_user
