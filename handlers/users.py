import asyncio
import json

import pydantic

import utils
from models.users import User, UserDocument, create_new_user


def create(event, context):
    """
    Create a new user upon registration
    """

    async def _create(event):
        await utils.setup()  # initialize connections to databases

        print(event)

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
            await create_new_user(new_user)
        except pydantic.ValidationError as e:
            return {
                "statusCode": 400,
                "body": json.dumps({"reason": e.errors()})
            }

        return {
            "statusCode": 200,
            "body": User(**new_user.dict()).json(exclude={"password", "scopes"})
        }

    return asyncio.run(_create(event))


def edit(event, context):
    asyncio.run(utils.setup())
    return {"statusCode": 200, "body": "Hello, World!"}


def show(event, context):
    asyncio.run(utils.setup())
    return {"statusCode": 200, "body": "Hello, World!"}


def follow(event, context):
    asyncio.run(utils.setup())
    return {"statusCode": 200, "body": "Hello, World!"}


def unfollow(event, context):
    asyncio.run(utils.setup())
    return {"statusCode": 200, "body": "Hello, World!"}
