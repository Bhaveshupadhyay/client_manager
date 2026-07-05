from fastapi import APIRouter
from backend.api.v1.chat import router as chat_router
from backend.api.v1.file import router as file_router

routers = APIRouter()

routers_list= [chat_router,file_router]
for router in routers_list:
    router.tags = routers.tags.append("v1")
    routers.include_router(router)