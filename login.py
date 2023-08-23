import json
import logging
from datetime import datetime, timedelta, timezone

import boto3
import jwt
from services.dynamodb import Users
from services.secrets import get_secret

def login(event, context):
    
    body = json.loads(event["body"])

    name = body.get("name")
    password = body.get("password")

    logging.info(f"{name=}")
    logging.info(f"{body=}")

    if not name or not password:
        return {
            'statusCode': 403,
            "body": json.dumps("Unauthorized: Name or password was not passed")
        }

    
    table = boto3.resource('dynamodb').Table("usersTable")
    users = Users(table)

    found_user = users.get_user(username=name)

    logging.info(f"{found_user=}")

    if found_user.get("password") != password:
        return {"statusCode": 403, "body": json.dumps({"reason": "incorrect password"})}
    
    payload = {
        "username": name,
        "scope": found_user.get("scope"),
        "exp": datetime.now(tz=timezone.utc) + timedelta(days=1)
    }

    token = jwt.encode(payload=payload, key=get_secret())
    
    body = {
        "token": token
    }

    response = {"statusCode": 200, "body": json.dumps(body)}

    return response


