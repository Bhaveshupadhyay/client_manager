import logging

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from backend.api.router import routers as v1_router
from backend.core.config import config
from backend.core.lifecycle import app_lifespan

logging.basicConfig(level=logging.INFO)
app = FastAPI(title=config.PROJECT_NAME, version="1.0.0",lifespan=app_lifespan)

app.include_router(v1_router, prefix=config.API_V1_STR)

origins = [
    "https://clientmanger.tech",
    "https://www.clientmanger.tech",
    "https://chat.clientmanger.tech",
    "http://127.0.0.1:8000",
    "http://localhost:8000"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key", "accept"],
)

@app.get("/")
def health_check():
    return {"status": "healthy"}