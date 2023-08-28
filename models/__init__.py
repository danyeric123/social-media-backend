from datetime import datetime

from beanie import Document
from bson import ObjectId


class BaseDocument(Document):

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            ObjectId: lambda oid: str(oid),
        }
