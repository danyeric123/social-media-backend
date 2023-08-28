import asyncio
import json

import jwt

import utils
from models.posts import get_recent_posts
from models.users import get_following
from services.secrets import get_secret


def index(event, context):
    try:
        header = event["headers"]["authorization-token"]
    except KeyError:
        return {"statusCode": 403, "body": "Unauthorized: No token was passed"}

    try:
        payload = jwt.decode(header, get_secret(), algorithms=["HS256"])
    except jwt.exceptions.InvalidSignatureError:
        return {"statusCode": 403, "body": "Unauthorized: Invalid token"}

    asyncio.run(utils.setup())
    # get friends
    friends = get_following(payload["username"])

    # get posts by friends
    posts = asyncio.run(get_recent_posts([friend.uuid for friend in friends]))

    return {"statusCode": 200, "body": json.dumps(posts)}


def create(event, context):
    asyncio.run(utils.setup())
    return {"statusCode": 200, "body": "Hello, World!"}


def get(event, context):
    asyncio.run(utils.setup())
    return {"statusCode": 200, "body": "Hello, World!"}


def edit(event, context):
    asyncio.run(utils.setup())
    return {"statusCode": 200, "body": "Hello, World!"}


def delete(event, context):
    asyncio.run(utils.setup())
    return {"statusCode": 200, "body": "Hello, World!"}

def like(event, context):
    asyncio.run(utils.setup())
    return {"statusCode": 200, "body": "Hello, World!"}

def unlike(event, context):
    asyncio.run(utils.setup())
    return {"statusCode": 200, "body": "Hello, World!"}

def comment(event, context):
    asyncio.run(utils.setup())
    return {"statusCode": 200, "body": "Hello, World!"}

