import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from azure.cosmos.aio import CosmosClient

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    cosmos_client = CosmosClient(
        os.getenv("COSMOS_ENDPOINT"),
        credential=os.getenv("COSMOS_KEY")
    )
    app.state.cosmos_db = cosmos_client.get_database_client(os.getenv("COSMOS_DATABASE"))

    yield
    await cosmos_client.close()