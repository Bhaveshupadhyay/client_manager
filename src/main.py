from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from backend.api.v1.auth import router as auth_router
from backend.api.v1.chat import router as chat_router
from backend.api.v1.webchat import router as webchat_router
from backend.core.lifecycle import app_lifespan

app = FastAPI(title="My Ai Client Manger", version="1.0.0", lifespan=app_lifespan)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(webchat_router, prefix="/api/v1")

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def health_check():
    return {"status": "healthy"}

@app.get("/webchat")
async def get_chat_page():
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"))