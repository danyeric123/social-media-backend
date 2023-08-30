from datetime import datetime

from beanie.operators import In
from pydantic import BaseModel

from models import BaseDocument

from .users import User


class Reply(BaseModel):
    user: str
    content: str
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    likes: list[str] = []
    replies: list["Reply"] = []


class Post(BaseModel):
    title: str
    author: str
    content: str
    categories: list[str] = []
    likes: list[str] = []
    replies: list[Reply] = []
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class PostDocument(BaseDocument, Post):

    class Settings:
        name = "posts"
        indexes = [("title",), ("user",)]


async def get_recent_posts(following: list[str] = []):
    return await PostDocument.find(In(PostDocument.author, following)).to_list()
