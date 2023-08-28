import json

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from neomodel import config

from config import CONFIG
from models.posts import PostDocument
from models.users import UserDocument

config.DATABASE_URL = f'bolt://{CONFIG.neo4j_username}:{CONFIG.neo4j_password}@{CONFIG.neo4j_uri}'


async def setup():
    """ Initialize connections to databases """
    db = AsyncIOMotorClient(CONFIG.mongo_uri).social_media
    await init_beanie(db, document_models=[UserDocument, PostDocument])