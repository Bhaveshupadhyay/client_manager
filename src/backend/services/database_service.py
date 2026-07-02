from fastapi import Request

from azure.cosmos import exceptions
import datetime

from azure.cosmos.aio import ContainerProxy
from fastapi import HTTPException

from backend.models.client import ProjectItem, ExtractedFacts
from backend.services.redis_service import cached







