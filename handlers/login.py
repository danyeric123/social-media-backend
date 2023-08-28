import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone

import jwt
import pydantic

import utils
from models.users import UserIn, find_user
from services.secrets import get_secret


def handler(event, context):
    """
    This is the handler for the login endpoint. It is responsible for
    authenticating a user and returning a JWT token that can be used to
    authenticate future requests.
    """

    async def _login(event):
        try:
            body = json.loads(event["body"])
        except KeyError:
            return {
                "statusCode": 403,
                "body": json.dumps("Unauthorized: No body was passed")
            }

        await utils.setup()
        try:
            user_request = UserIn.parse_obj(body)
        except pydantic.ValidationError as e:
            return {
                "statusCode": 403,
                "body": json.dumps({"reason": e.errors()})
            }

        found_user = await find_user(user_request.username)

        print(f"found user: {found_user}")

        if found_user.password != user_request.password.get_secret_value():
            return {
                "statusCode": 403,
                "body": json.dumps({"reason": "incorrect password"})
            }

        payload = {
            "username": found_user.username,
            "scope": found_user.scopes,
            "exp": datetime.now(tz=timezone.utc) + timedelta(days=1)
        }

        token = jwt.encode(payload=payload, key=get_secret())

        body = {"token": token}

        response = {"statusCode": 200, "body": json.dumps(body)}

        return response

    return asyncio.run(_login(event))
