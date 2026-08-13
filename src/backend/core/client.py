import urllib.parse

from azure.cosmos.aio import CosmosClient
from upstash_redis.asyncio import Redis
from qdrant_client import QdrantClient
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.core.config import config

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

_postgres_engine: AsyncEngine | None = None
_postgres_client: async_sessionmaker[AsyncSession] | None = None
_redis_client: Redis | None = None
_cosmos_client: CosmosClient | None = None
_qdrant_client: QdrantClient | None = None
Base = declarative_base()

def get_postgres_client() -> async_sessionmaker[AsyncSession]:
    global _postgres_engine, _postgres_client
    if _postgres_client is None:
        raw_password = config.POSTGRES_DB_PASSWORD
        encoded_password = urllib.parse.quote_plus(raw_password)

        raw_user = config.POSTGRES_DB_USER
        encoded_user = urllib.parse.quote_plus(raw_user)

        db_host = config.POSTGRES_DB_HOST
        db_name = config.POSTGRES_DB_NAME or "postgres"
        db_port = config.POSTGRES_DB_PORT or "5432"

        ASYNC_SQLALCHEMY_DATABASE_URL = (
            f"postgresql+asyncpg://{encoded_user}:{encoded_password}@{db_host}:{db_port}/{db_name}?ssl=require"
        )

        _postgres_engine = create_async_engine(
            ASYNC_SQLALCHEMY_DATABASE_URL,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False,
        )

        _postgres_client = async_sessionmaker(
            bind=_postgres_engine,
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _postgres_client


def get_redis_client() -> Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis(
            url=config.UPSTASH_REDIS_REST_URL, 
            token=config.UPSTASH_REDIS_REST_TOKEN
        )
    return _redis_client

def get_cosmos_client() -> CosmosClient:
    global _cosmos_client
    if _cosmos_client is None:
        _cosmos_client = CosmosClient(
            config.COSMOS_ENDPOINT,
            credential=config.COSMOS_KEY
        )
    return _cosmos_client

def get_qdrant_client() -> QdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(
            url=config.QDRANT_ENDPOINT,
            api_key=config.QDRANT_KEY,
        )
    return _qdrant_client

def open_connection() -> None:
    get_cosmos_client()
    get_redis_client()
    get_postgres_client()


async def close_redis_client() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


async def close_postgres_client() -> None:
    global _postgres_engine, _postgres_client
    if _postgres_engine is not None:
        await _postgres_engine.dispose()
        _postgres_engine = None
        _postgres_client = None

async def close_cosmos_client() -> None:
    global _cosmos_client
    if _cosmos_client is not None:
        await _cosmos_client.close()
        _cosmos_client = None

async def close_connection():
    await close_redis_client()
    await close_postgres_client()
    await close_cosmos_client()