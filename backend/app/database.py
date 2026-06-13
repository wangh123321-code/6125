from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import redis.asyncio as redis
from app.config import settings

mongodb_client: AsyncIOMotorClient | None = None
redis_client: redis.Redis | None = None
db: AsyncIOMotorDatabase | None = None


def get_mongodb_client() -> AsyncIOMotorClient:
    global mongodb_client
    if mongodb_client is None:
        mongodb_client = AsyncIOMotorClient(settings.MONGODB_URL, tz_aware=True)
    return mongodb_client


def get_database() -> AsyncIOMotorDatabase:
    global db
    if db is None:
        client = get_mongodb_client()
        db = client[settings.MONGODB_DB_NAME]
    return db


def get_redis_client() -> redis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return redis_client


async def close_mongodb_connection():
    global mongodb_client, db
    if mongodb_client is not None:
        mongodb_client.close()
        mongodb_client = None
        db = None


async def close_redis_connection():
    global redis_client
    if redis_client is not None:
        await redis_client.close()
        redis_client = None


get_redis = get_redis_client
