import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from azure.cosmos.aio import CosmosClient
from redis.asyncio.cluster import RedisCluster

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    cosmos_client = CosmosClient(
        os.getenv("COSMOS_ENDPOINT"),
        credential=os.getenv("COSMOS_KEY")
    )
    app.state.cosmos_db = cosmos_client.get_database_client(os.getenv("COSMOS_DATABASE"))
    app.state.redis = RedisCluster(
        host=os.getenv("AZURE_REDIS_ENDPOINT"),
        port=10000,
        password=os.getenv("AZURE_REDIS_KEY"),
        ssl=True,
        ssl_cert_reqs="none",
        decode_responses=True
    )

    yield
    await cosmos_client.close()
    await app.state.redis.close()