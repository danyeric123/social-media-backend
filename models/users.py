import re
from typing import Optional

import pydantic
from beanie import Indexed
from neo4j import GraphDatabase, basic_auth
from neomodel import RelationshipTo, StringProperty, StructuredNode
from pydantic.types import SecretStr

from config import CONFIG
from models import BaseDocument

driver = GraphDatabase.driver(f'bolt://{CONFIG.neo4j_uri}',
                              auth=basic_auth(CONFIG.neo4j_username,
                                              CONFIG.neo4j_password))


class UserIn(pydantic.BaseModel):
    username: str
    password: SecretStr


class User(pydantic.BaseModel):
    username: Indexed(str, unique=True)
    password: SecretStr
    scopes: list[str] = []
    avatar: Optional[str] = ""

    @pydantic.validator("avatar")
    def avatar_must_be_url(cls, v):
        if not v:
            return v
        # Define a regular expression pattern to match URLs
        url_pattern = r'^https?://(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,6}(?:/[^/]*)*(?:\.(?:jpg|jpeg|png|gif))$'
        if "s3.amazonaws.com" not in v or not re.match(url_pattern, v):
            raise ValueError(f"Avatar must be a url. Received: {v}")
        return v


class UserDocument(User, BaseDocument):
    password: str

    class Settings:
        name = "users"
        indexes = [("id",), ("username",)]


class UserNode(StructuredNode):
    username = StringProperty()
    uuid = StringProperty(unique_index=True)
    avatar = StringProperty()
    following = RelationshipTo("UserNode", "FOLLOWS")


async def create_new_user(new_user: UserDocument):
    await new_user.save()
    UserNode(username=new_user.username,
             uuid=str(new_user.id),
             avatar=new_user.avatar).save()
    return new_user


def get_followers(username: str):

    with driver.session() as session:
        result = session.execute_read(
            lambda tx: tx.run("""
            MATCH (user:UserNode {username: $username})<-[:FOLLOWS]-(follower:UserNode)
            RETURN follower.username as username, follower.avatar as avatar, follower.uuid as uuid
            """,
                              username=username).data())
        return [dict(record) for record in result]


def get_following(username: str):

    with driver.session() as session:
        result = session.execute_read(
            lambda tx: tx.run("""
              MATCH (user:UserNode {username: $username})-[:FOLLOWS]->(following:UserNode)
              RETURN following.username as username, following.avatar as avatar, following.uuid as uuid
              """,
                              username=username).data())
        return [dict(record) for record in result]


def get_mutual_frields(username: str, other_username: str):

    with driver.session() as session:
        result = session.execute_read(
            lambda tx: tx.run("""
            MATCH (user:UserNode {username: $username})-[:FOLLOWS]->(mutual:UserNode)<-[:FOLLOWS]-(other:UserNode {username: $other_username})
            RETURN mutual.username as username, mutual.avatar as avatar, mutual.uuid as uuid
            """,
                              username=username,
                              other_username=other_username).data())
        return [dict(record) for record in result]


async def find_user(username: str) -> UserDocument:
    found_user = await UserDocument.find_one({"username": username})
    return found_user
