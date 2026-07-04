import logging

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from backend.api.v1.auth import router as auth_router
from backend.api.v1.chat import router as chat_router
from backend.api.v1.file import router as file_router
from backend.core.lifecycle import app_lifespan

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="My Ai Client Manger", version="1.0.0",lifespan=app_lifespan)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(file_router, prefix="/api/v1")

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