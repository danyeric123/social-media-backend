import asyncio
import json

import pydantic

import utils
from models.users import (User, UserDocument, UserUpdate, get_followers,
                          get_following)
from utils.logging import LOG_MANAGER

logger = LOG_MANAGER.getLogger(__name__)


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
                    "body": json.dumps({"reason": "username already exists"}),
                }
            logger.info(
                f"Creating user '{new_user.username}'",
                extra={},
            )
            await new_user.save()
        except pydantic.ValidationError as e:
            return {
                "statusCode": 400,
                "body": json.dumps({"reason": e.errors()})
            }

        return {
            "statusCode":
                200,
            "body":
                User(**new_user.dict()).json(exclude={"password", "scopes"}),
        }

    return asyncio.run(_create(event))


def index(event, context):

    async def _index():
        await utils.setup()
        users = await UserDocument.find_all(limit=100,
                                            sort=[("username", 1)]).to_list()

        logger.info(f"Found {len(users)} users", extra={})
        return {
            "statusCode":
                200,
            "users": [
                User(**user.dict()).json(exclude={"password", "scopes"})
                for user in users
            ],
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
            logger.info(
                f"Updated user {username} with {body}",
                extra={},
            )
        except pydantic.ValidationError as e:
            logger.error(
                f"Failed to update user {username}: {e}",
                extra={},
            )
            return {
                "statusCode": 400,
                "body": json.dumps({"reason": e.errors()})
            }

        return {
            "statusCode": 200,
            "body": User(**user.dict()).json(exclude={"password", "scopes"}),
        }

    return asyncio.run(_edit(event))


def show(event, context):

    async def _show(event):
        await utils.setup()
        username = event["pathParameters"]["username"]
        user = await UserDocument.find_one(UserDocument.username == username)

        if not user:
            logger.error(
                f"Failed to find user {username}",
                extra={},
            )
            return {"statusCode": 404, "body": "User not found"}

        logger.info(f"Found user {username}", extra={})
        logger.info(
            f"Getting followers for {username}",
            extra={},
        )
        followers = await get_followers(username)
        user.followers = followers
        following = await get_following(username)
        user.following = following

        return {
            "statusCode": 200,
            "body": User(**user.dict()).json(exclude={"password", "scopes"}),
        }

    return asyncio.run(_show(event))


def follow(event, context):

    async def _follow(event):
        await utils.setup()

        follower = utils.get_current_user(event, context)

        follower = await UserDocument.find_one(UserDocument.username == follower
                                              )

        if not follower:
            return {"statusCode": 404, "body": "User in request not found"}

        username = event["pathParameters"]["username"]
        follow_user = await UserDocument.find_one(
            UserDocument.username == username)

        if not follow_user:
            return {"statusCode": 404, "body": "User not found"}

        logger.info(
            f"User '{follower.username}' wants to follow {follow_user.username}",
            extra={},
        )

        if follower == username:
            return {"statusCode": 400, "body": "Cannot follow yourself"}

        if follower.username in follow_user.followers:
            logger.info(
                f"User '{follower.username}' already follows '{follow_user.username}'",
                extra={},
            )
            return {"statusCode": 200, "body": json.dumps({})}

        follow_user.followers.append(follower.username)

        await follow_user.save()

        follower.following.append(follow_user.username)

        await follower.save()

        follow_user = {
            **follow_user.dict(),
            "followers":
                await get_followers(follow_user.followers),
            "following":
                await get_following(follow_user.following),
        }

        return {
            "statusCode": 200,
            "body": User(**follow_user).json(exclude={"password", "scopes"}),
        }

    return asyncio.run(_follow(event))


def unfollow(event, context):

    async def _unfollow(event):
        await utils.setup()

        follower = utils.get_current_user(event, context)

        follower = await UserDocument.find_one(UserDocument.username == follower
                                              )

        if not follower:
            return {"statusCode": 404, "body": "User in request not found"}

        username = event["pathParameters"]["username"]
        follow_user = await UserDocument.find_one(
            UserDocument.username == username)

        if not follow_user:
            return {"statusCode": 404, "body": "User not found"}

        if follower == username:
            return {"statusCode": 400, "body": "Cannot unfollow yourself"}

        if follower.username not in follow_user.followers:
            logger.info(
                f"User '{follower.username}' does not follow {follow_user.username}",
                extra={},
            )
            return {"statusCode": 200, "body": json.dumps({})}

        logger.info(
            f"User '{follower.username}' wants to unfollow {follow_user.username}",
            extra={},
        )

        follow_user.followers.remove(follower.username)

        await follow_user.save()

        follower.following.remove(follow_user.username)

        await follower.save()

        follow_user = {
            **follow_user.dict(),
            "followers": await get_followers(username),
            "following": await get_following(username),
        }

        return {
            "statusCode": 200,
            "body": User(**follow_user).json(exclude={"password", "scopes"}),
        }

    return asyncio.run(_unfollow(event))
