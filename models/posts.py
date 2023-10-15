from datetime import datetime

from beanie.operators import In
from pydantic import BaseModel, validator
from ulid import ULID

from models import BaseDocument
from models.users import UserDocument


class Reply(BaseModel):
    ulid: str
    author: str
    content: str
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    likes: list[str] = []
    # parent_ulid: str

    @validator("ulid")
    def ulid_must_be_valid(cls, v):
        if isinstance(v, str):
            try:
                ULID.from_str(v)
                return v
            except ValueError:
                raise ValueError("ULID must be a valid ULID string")
        raise ValueError("ULID must be a string or a ULID object")


class Post(BaseModel):
    ulid: str
    title: str
    author: str
    content: str
    categories: list[str] = []
    likes: list[str] = []
    replies: list[Reply] = []
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    @validator("ulid")
    def ulid_must_be_valid(cls, v):
        if isinstance(v, str):
            try:
                ULID.from_str(v)
                return v
            except ValueError:
                raise ValueError("ULID must be a valid ULID string")
        raise ValueError("ULID must be a string or a ULID object")


class PostDocument(BaseDocument, Post):

    class Settings:
        name = "posts"
        indexes = [("title",), ("user",), ("ulid",)]


async def get_recent_posts(user: UserDocument) -> list[PostDocument]:
    all_posts = []
    user_posts = await PostDocument.find(PostDocument.author == user.username
                                        ).to_list()
    all_posts.extend(user_posts)
    following_posts = await PostDocument.find(
        In(PostDocument.author, user.following)).to_list()
    all_posts.extend(following_posts)
    return all_posts
