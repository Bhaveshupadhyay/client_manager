import os
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from PIL import Image
import pytesseract
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.api.dependencies import get_current_account, get_file_service
from backend.models.account import Account
from datetime import datetime, timedelta, UTC

from backend.services.file_service import FileService

router = APIRouter(prefix='/file', tags=['File'])

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
)

@router.post("/upload")
async def upload_file(
        file: UploadFile = File(...),
        file_service: FileService = Depends(get_file_service),
        account: Account = Depends(get_current_account)
):
    response= await file_service.convert_to_chunks(file=file)
    return response