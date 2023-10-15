import asyncio
import json
from datetime import datetime

import jwt
import pydantic
from ulid import ULID

import utils
from models import serialize_datetime
from models.posts import Post, PostDocument, Reply, get_recent_posts
from models.users import UserDocument
from utils.logging import LOG_MANAGER

logger = LOG_MANAGER.getLogger(__name__)


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

        if "queryStringParameters" in event and event[
                "queryStringParameters"] and "category" in event[
                    "queryStringParameters"]:
            posts = await PostDocument.find(
                PostDocument.categories == event["queryStringParameters"]
                ["category"]).to_list()
            return {
                "statusCode":
                    200,
                "body":
                    json.dumps(
                        {
                            "posts":
                                [Post(**post.dict()).dict() for post in posts]
                        },
                        default=serialize_datetime),
            }

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

    async def _edit(event):
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
        try:
            body = json.loads(event["body"])
        except KeyError:
            return {"statusCode": 400, "body": json.dumps("No body was passed")}

        try:
            post_ulid = event["pathParameters"]["id"]
        except KeyError:
            return {
                "statusCode":
                    400,
                "body":
                    json.dumps(
                        {"message": "Path parameter 'id' was not passed"})
            }

        logger.info(f"Editing post {post_ulid} with {body}", extra={})

        try:
            post = await PostDocument.find_one(PostDocument.ulid == post_ulid)
            if not post:
                return {"statusCode": 404, "body": "Post not found"}
            if post.author != username:
                return {"statusCode": 403, "body": "Unauthorized"}

            for field, value in body.items():
                setattr(post, field, value)

            await post.save()
        except pydantic.ValidationError as e:
            logger.error(f"{post} caused a validation error: {e.errors()}",
                         extra={})
            return {
                "statusCode": 400,
                "body": json.dumps({"reason": e.errors()})
            }

        return {"statusCode": 200, "body": Post(**post.dict()).json()}

    return asyncio.run(_edit(event))


def delete(event, context):

    async def _delete(event):
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
        try:
            post_ulid = event["pathParameters"]["id"]
        except KeyError:
            return {
                "statusCode":
                    400,
                "body":
                    json.dumps(
                        {"message": "Path parameter 'id' was not passed"})
            }

        logger.info(f"Deleting post {post_ulid}", extra={})

        try:
            post = await PostDocument.find_one(PostDocument.ulid == post_ulid)
            if not post:
                return {"statusCode": 404, "body": "Post not found"}
            if post.author != username:
                return {"statusCode": 403, "body": "Unauthorized"}

            await post.delete()
        except pydantic.ValidationError as e:
            logger.error(f"{post} caused a validation error: {e.errors()}",
                         extra={})
            return {
                "statusCode": 400,
                "body": json.dumps({"reason": e.errors()})
            }

        return {"statusCode": 200, "body": Post(**post.dict()).json()}

    return asyncio.run(_delete(event))


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


def comment_like(event, context):

    async def _comment_like(event):
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
        comment_id = event["pathParameters"]["comment_id"]

        post = await PostDocument.find_one(PostDocument.ulid == post_id)
        if not post:
            return {"statusCode": 404, "body": "Post not found"}

        comment = next(
            filter(lambda reply: reply.ulid == comment_id, post.replies), None)
        if not comment:
            return {"statusCode": 404, "body": "Comment not found"}

        if username in comment.likes:
            return {"statusCode": 200}

        comment.likes.append(username)
        await post.save()
        return {"statusCode": 200}

    return asyncio.run(_comment_like(event))


def comment_unlike(event, context):

    async def _comment_unlike(event):
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
        comment_id = event["pathParameters"]["comment_id"]

        post = await PostDocument.find_one(PostDocument.ulid == post_id)
        if not post:
            return {"statusCode": 404, "body": "Post not found"}

        comment = next(
            filter(lambda reply: reply.ulid == comment_id, post.replies), None)
        if not comment:
            return {"statusCode": 404, "body": "Comment not found"}

        if username not in comment.likes:
            return {"statusCode": 200}

        comment.likes.remove(username)
        await post.save()
        return {"statusCode": 200}

    return asyncio.run(_comment_unlike(event))


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
            # If the body contains the parent_ulid, it's a reply
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

def comment_delete(event, context):
    
        async def _comment_delete(event):
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
            comment_id = event["pathParameters"]["commentId"]
    
            post = await PostDocument.find_one(PostDocument.ulid == post_id)
            if not post:
                return {"statusCode": 404, "body": "Post not found"}
    
            comment = next(
                filter(lambda reply: reply.ulid == comment_id, post.replies), None)
            if not comment:
                return {"statusCode": 404, "body": "Comment not found"}
    
            if comment.author != username:
                return {"statusCode": 403, "body": "Unauthorized"}
    
            post.replies.remove(comment)
            await post.save()
            return {"statusCode": 200}
    
        return asyncio.run(_comment_delete(event))
