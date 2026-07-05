import os
import urllib.parse

from azure.cosmos.aio import CosmosClient
from dotenv import load_dotenv
from upstash_redis.asyncio import Redis
from qdrant_client import QdrantClient
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

_postgres_client: sessionmaker | None = None
_redis_client: Redis | None = None
_cosmos_client: CosmosClient | None = None
_qdrant_client: QdrantClient | None = None
Base = declarative_base()

def get_postgres_client() -> sessionmaker:
    global _postgres_client
    if _postgres_client is None:
        raw_password = os.getenv("POSTGRES_DB_PASSWORD", "")
        encoded_password = urllib.parse.quote_plus(raw_password)

        DB_HOST = os.getenv("POSTGRES_DB_HOST", "")

        SQLALCHEMY_DATABASE_URL = f"postgresql://postgres.ksvunxoiwtrsvujhkpxx:{encoded_password}@{DB_HOST}:5432/postgres?sslmode=require"

        engine = create_engine(SQLALCHEMY_DATABASE_URL)

        _postgres_client = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _postgres_client


def get_redis_client() -> Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_env()
    return _redis_client

def get_cosmos_client() -> CosmosClient:
    global _cosmos_client
    if _cosmos_client is None:
        cosmos_client = CosmosClient(
            os.getenv("COSMOS_ENDPOINT"),
            credential=os.getenv("COSMOS_KEY")
        )
    return cosmos_client

def get_qdrant_client() -> QdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        qdrant_client = QdrantClient(
            url=os.getenv("QDRANT_ENDPOINT"),
            api_key=os.getenv("QDRANT_KEY"),
        )
    return qdrant_client
def open_connection() -> None:
    get_cosmos_client()
    get_redis_client()
    get_postgres_client()


async def close_redis_client() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


def close_postgres_client() -> None:
    global _postgres_client
    if _postgres_client is not None:
        _postgres_client.close_all()
        _postgres_client = None

async def close_cosmos_client() -> None:
    global _cosmos_client
    if _cosmos_client is not None:
        await _cosmos_client.close()
        _cosmos_client = None

async def close_connection():
    await close_redis_client()
    close_postgres_client()
    await close_cosmos_client()