import asyncio
import json

import jwt
import pydantic

import utils
from models.posts import Post, PostDocument, Reply, get_recent_posts
from models.users import UserDocument
from services.secrets import get_secret


def get_current_user(event):
    header = event["headers"]["authorization-token"]
    payload = jwt.decode(header, get_secret(), algorithms=["HS256"])
    return payload["username"]


def index(event, context):
    """
    Get recent posts from the user's following list
    """

    try:
        username = get_current_user(event)
    except KeyError:
        return {"statusCode": 403, "body": "Unauthorized: No token was passed"}
    except jwt.exceptions.InvalidSignatureError:
        return {"statusCode": 403, "body": "Unauthorized: Invalid token"}

    async def _index(username: str):
        await utils.setup()
        user = await UserDocument.find_one(UserDocument.username == username)

        if not user:
            return {"statusCode": 404, "body": "User not found"}

        posts = get_recent_posts(user.following)
        return {
            "statusCode": 200,
            "body": [Post(**post.dict()).json() for post in posts]
        }

    return asyncio.run(_index(username))


def create(event, context):
    """
    Create a new post
    """

    try:
        username = get_current_user(event)
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
            new_post = PostDocument(**body, author=username)
            await new_post.save()
        except pydantic.ValidationError as e:
            return {
                "statusCode": 400,
                "body": json.dumps({"reason": e.errors()})
            }

        return {"statusCode": 200, "body": Post(**new_post.dict()).json()}

    return asyncio.run(_create(event, username))


def get(event, context):

    async def _get(event):
        await utils.setup()
        try:
            post = await PostDocument.find_one(
                PostDocument.id == event["pathParameters"]["id"])
        except KeyError:
            return {
                "statusCode":
                    400,
                "body":
                    json.dumps(
                        {"message": "Path parameter 'id' was not passed"})
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
            username = get_current_user(event)
        except KeyError:
            return {
                "statusCode": 403,
                "body": "Unauthorized: No token was passed"
            }
        except jwt.exceptions.InvalidSignatureError:
            return {"statusCode": 403, "body": "Unauthorized: Invalid token"}

        await utils.setup()

        post_id = event["pathParameters"]["id"]

        post = await PostDocument.find_one(PostDocument.id == post_id)
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
            username = get_current_user(event)
        except KeyError:
            return {
                "statusCode": 403,
                "body": "Unauthorized: No token was passed"
            }
        except jwt.exceptions.InvalidSignatureError:
            return {"statusCode": 403, "body": "Unauthorized: Invalid token"}

        await utils.setup()

        post_id = event["pathParameters"]["id"]

        post = await PostDocument.find_one(PostDocument.id == post_id)
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
            username = get_current_user(event)
        except KeyError:
            return {
                "statusCode": 403,
                "body": "Unauthorized: No token was passed"
            }
        except jwt.exceptions.InvalidSignatureError:
            return {"statusCode": 403, "body": "Unauthorized: Invalid token"}

        await utils.setup()

        post_id = event["pathParameters"]["id"]

        post = await PostDocument.find_one(PostDocument.id == post_id)
        if not post:
            return {"statusCode": 404, "body": "Post not found"}

        try:
            reply = Reply.parse_obj(json.loads(event["body"]))
        except KeyError:
            return {"statusCode": 400, "body": "No body was passed"}

        post.comments.append(reply)
        await post.save()
        return {"statusCode": 200}

    return asyncio.run(_comment(event))
