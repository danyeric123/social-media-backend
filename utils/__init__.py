import jwt
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from neomodel import config

from config import CONFIG
from models.posts import PostDocument
from models.users import UserDocument
from services.secrets import get_secret
from utils.logging import LOG_MANAGER

config.DATABASE_URL = (
    f"bolt://{CONFIG.neo4j_username}:{CONFIG.neo4j_password}@{CONFIG.neo4j_uri}"
)

logger = LOG_MANAGER.getLogger(__name__)


async def setup():
    """Initialize connections to databases"""
    db = AsyncIOMotorClient(CONFIG.mongo_uri).social_media
    logger.info("Initializing Beanie")
    await init_beanie(db, document_models=[UserDocument, PostDocument])


def get_current_user(event: dict, context) -> str:
    """Get the current user from the JWT token"""

    logger.info(
        f"Grabbing user from token: {event['headers']['authorization-token']}",
        extra={},
    )
    header = event["headers"]["authorization-token"]
    payload = jwt.decode(header, get_secret(), algorithms=["HS256"])
    return payload["username"]
