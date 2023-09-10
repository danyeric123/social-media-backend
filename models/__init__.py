import json
from datetime import datetime
from typing import Union

from beanie import Document
from bson import ObjectId
from pydantic import BaseModel, validator


class BaseDocument(Document):

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            ObjectId: lambda oid: str(oid),
        }


class Response(BaseModel):
    statusCode: int
    body: Union[str, dict, BaseModel] = ""
    headers: dict = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': True,
    }

    @validator('statusCode')
    def statusCode_must_be_valid(cls, v):
        if not isinstance(v, int) and 200 < v < 599:
            raise ValueError("Not a valid status code")
        return v

    @validator('body')
    def body_must_be_valid(cls, v):
        if isinstance(v, BaseModel):
            return v.json()
        if isinstance(v, str):
            return v
        if isinstance(v, dict):
            return json.dumps(v)
        raise ValueError("Body must be a string or a BaseModel")
