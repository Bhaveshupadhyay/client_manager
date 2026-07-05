from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.core.client import open_connection,close_connection

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    open_connection()
    yield
    await close_connection()