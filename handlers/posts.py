import asyncio
import json
from datetime import datetime

import jwt
import pydantic
from ulid import ULID

import utils
from models.posts import Post, PostDocument, Reply, get_recent_posts
from models.users import UserDocument
from utils.logging import LOG_MANAGER

logger = LOG_MANAGER.getLogger(__name__)


def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def index(event, context):
    """
    Get recent posts from the user's following list
    """

    try:
        username = utils.get_current_user(event, context)
    except KeyError:
        return {"statusCode": 403, "body": "Unauthorized: No token was passed"}
    except jwt.exceptions.InvalidSignatureError:
        return {"statusCode": 403, "body": "Unauthorized: Invalid token"}

    async def _index(username: str):
        await utils.setup()
        user = await UserDocument.find_one(UserDocument.username == username)

        if not user:
            return {"statusCode": 404, "body": "User not found"}

        posts = await get_recent_posts(user)
        return {
            "statusCode":
                200,
            "body":
                json.dumps(
                    {"posts": [Post(**post.dict()).dict() for post in posts]},
                    default=serialize_datetime),
        }

    return asyncio.run(_index(username))


def create(event, context):
    """
    Create a new post
    """

    try:
        username = utils.get_current_user(event, context)
    except KeyError:
        return {"statusCode": 403, "body": "Unauthorized: No token was passed"}
    except jwt.exceptions.InvalidSignatureError:
        return {"statusCode": 403, "body": "Unauthorized: Invalid token"}

    async def _create(event, username: str):
        await utils.setup()
        try:
            body = json.loads(event["body"])
        except KeyError:
            return {"statusCode": 400, "body": json.dumps("No body was passed")}

        try:
            new_post = PostDocument(**body, author=username, ulid=str(ULID()))
            await new_post.save()
        except pydantic.ValidationError as e:
            logger.error(f"{new_post} caused a validation error: {e.errors()}",
                         extra={})
            return {
                "statusCode": 400,
                "body": json.dumps({"reason": e.errors()})
            }

        return {"statusCode": 200, "body": Post(**new_post.dict()).json()}

    return asyncio.run(_create(event, username))


def get(event, context):

    async def _get(event):
        await utils.setup()
        logger.info(f"Getting post {event['pathParameters']['id']}", extra={})
        try:
            _id = event["pathParameters"]["id"]
            post = await PostDocument.find_one(PostDocument.ulid == _id)
        except KeyError:
            return {
                "statusCode":
                    400,
                "body":
                    json.dumps(
                        {"message": "Path parameter 'id' was not passed"}),
            }

        if not post:
            return {"statusCode": 404, "body": "Post not found"}

        return {"statusCode": 200, "body": Post(**post.dict()).json()}

    return asyncio.run(_get(event))


def edit(event, context):
    asyncio.run(utils.setup())
    return {"statusCode": 200, "body": "Hello, World!"}


def delete(event, context):
    asyncio.run(utils.setup())
    return {"statusCode": 200, "body": "Hello, World!"}


def like(event, context):

    async def _like(event):
        try:
            username = utils.get_current_user(event, context)
        except KeyError:
            return {
                "statusCode": 403,
                "body": "Unauthorized: No token was passed"
            }
        except jwt.exceptions.InvalidSignatureError:
            return {"statusCode": 403, "body": "Unauthorized: Invalid token"}

        await utils.setup()

        post_id = event["pathParameters"]["id"]

        post = await PostDocument.find_one(PostDocument.ulid == post_id)
        if not post:
            return {"statusCode": 404, "body": "Post not found"}

        if username in post.likes:
            return {"statusCode": 200}

        post.likes.append(username)
        await post.save()
        return {"statusCode": 200}

    return asyncio.run(_like(event))


def unlike(event, context):

    async def _unlike(event):
        try:
            username = utils.get_current_user(event, context)
        except KeyError:
            return {
                "statusCode": 403,
                "body": "Unauthorized: No token was passed"
            }
        except jwt.exceptions.InvalidSignatureError:
            return {"statusCode": 403, "body": "Unauthorized: Invalid token"}

        await utils.setup()

        post_id = event["pathParameters"]["id"]

        post = await PostDocument.find_one(PostDocument.ulid == post_id)
        if not post:
            return {"statusCode": 404, "body": "Post not found"}

        if username not in post.likes:
            return {"statusCode": 200}

        post.likes.remove(username)
        await post.save()
        return {"statusCode": 200}

    return asyncio.run(_unlike(event))


def comment(event, context):

    async def _comment(event):
        try:
            username = utils.get_current_user(event, context)
        except KeyError:
            return {
                "statusCode": 403,
                "body": "Unauthorized: No token was passed"
            }
        except jwt.exceptions.InvalidSignatureError:
            return {"statusCode": 403, "body": "Unauthorized: Invalid token"}

        await utils.setup()

        post_id = event["pathParameters"]["id"]

        post = await PostDocument.find_one(PostDocument.ulid == post_id)
        if not post:
            return {"statusCode": 404, "body": "Post not found"}

        try:
            reply = Reply(**json.loads(event["body"]),
                          author=username,
                          ulid=str(ULID()))
        except KeyError:
            return {"statusCode": 400, "body": "No body was passed"}
        except pydantic.ValidationError as e:
            return {
                "statusCode": 400,
                "body": json.dumps({"reason": e.errors()})
            }

        post.replies.append(reply)
        await post.save()
        return {"statusCode": 200, "body": reply.json()}

    return asyncio.run(_comment(event))
