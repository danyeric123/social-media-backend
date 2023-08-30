import asyncio
import json

import pydantic

import utils
from models.users import User, UserDocument, UserUpdate, get_followers


def create(event, context):
    """
    Create a new user upon registration
    """

    async def _create(event):
        await utils.setup()  # initialize connections to databases

        try:
            body = json.loads(event["body"])
        except KeyError:
            return {"statusCode": 400, "body": json.dumps("No body was passed")}

        try:
            new_user = UserDocument.parse_obj(body)
            if await UserDocument.find_one(
                    UserDocument.username == new_user.username):
                return {
                    "statusCode": 400,
                    "body": json.dumps({"reason": "username already exists"})
                }
            await new_user.save()
        except pydantic.ValidationError as e:
            return {
                "statusCode": 400,
                "body": json.dumps({"reason": e.errors()})
            }

        followers = await get_followers(new_user.followers)
        following = await get_followers(new_user.following)

        return {
            "statusCode":
                200,
            "body":
                User(**new_user.dict(),
                     followers=followers,
                     following=following).json(exclude={"password", "scopes"})
        }

    return asyncio.run(_create(event))


def index(event, context):

    async def _index():
        await utils.setup()
        users = await UserDocument.find_all(limit=100,
                                            sort=[("username", 1)]).to_list()
        return {
            "statusCode":
                200,
            "users": [
                User(**user.dict()).json(exclude={"password", "scopes"})
                for user in users
            ]
        }

    return asyncio.run(_index())


def edit(event, context):

    async def _edit(event):
        await utils.setup()
        try:
            body = json.loads(event["body"])
        except KeyError:
            return {"statusCode": 400, "body": json.dumps("No body was passed")}

        username = event["pathParameters"]["username"]

        try:
            user = UserUpdate.parse_obj(body)
            await UserDocument.find_one(UserDocument.username == username
                                       ).update(**user.dict(exclude_none=True))
        except pydantic.ValidationError as e:
            return {
                "statusCode": 400,
                "body": json.dumps({"reason": e.errors()})
            }

        return {
            "statusCode": 200,
            "body": User(**user.dict()).json(exclude={"password", "scopes"})
        }

    return asyncio.run(_edit(event))


def show(event, context):

    async def _show(event):
        await utils.setup()
        username = event["pathParameters"]["username"]
        user = await UserDocument.find_one(UserDocument.username == username)

        if not user:
            return {"statusCode": 404, "body": "User not found"}

        return {
            "statusCode": 200,
            "body": User(**user.dict()).json(exclude={"password", "scopes"})
        }

    return asyncio.run(_show(event))


def follow(event, context):
    asyncio.run(utils.setup())
    return {"statusCode": 200, "body": "Hello, World!"}


def unfollow(event, context):
    asyncio.run(utils.setup())
    return {"statusCode": 200, "body": "Hello, World!"}
