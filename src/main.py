from fastapi import FastAPI
from backend.api.v1.auth import router as auth_router
from backend.api.v1.chat import router as chat_router

app = FastAPI(title="My Ai Client Manger", version="1.0.0")

app.include_router(auth_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")


@app.get("/")
def health_check():
    return {"status": "healthy"}
