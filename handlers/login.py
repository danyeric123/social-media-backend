import asyncio
import json
from datetime import datetime, timedelta, timezone

import jwt
import pydantic

import utils
from models import Response
from models.users import UserDocument, UserIn, find_user
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
            return Response(statusCode=403,
                            body="Unauthorized: No body was passed")

        await utils.setup()
        try:
            user_request = UserIn.parse_obj(body)
        except pydantic.ValidationError as e:
            return Response(statusCode=403, body={"reason": e.errors()})

        found_user = await find_user(user_request.username)

        print(f"found user: {found_user}")

        if found_user.password != user_request.password.get_secret_value():
            return Response(statusCode=403,
                            body={"reason": "incorrect password"})

        token = utils.generate_token(found_user)

        return Response(statusCode=200, body={"token": token})

    res = asyncio.run(_login(event))
    return res.dict()
