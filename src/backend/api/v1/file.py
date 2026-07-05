from fastapi import APIRouter, UploadFile, File, Depends, Form
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.core.dependencies import get_current_account, get_file_service
from backend.models.account import Account
from backend.schemas.file import FileCheckResponse
from backend.schemas.qdrant import UploadedFileResponse

from backend.services.file_service import FileService

router = APIRouter(prefix='/file', tags=['File'])

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
)

@router.get("/check", response_model=FileCheckResponse)
async def check_file_exists(
        project_id: str,
        filename: str,
        file_service: FileService = Depends(get_file_service),
        account: Account = Depends(get_current_account)
):
    return file_service.check_if_file_exists(filename=filename,project_id=project_id)


@router.post("/upload",response_model=UploadedFileResponse)
async def upload_file(
        project_id: str = Form(...),
        overwrite: bool = Form(False),
        file: UploadFile = File(...),
        file_service: FileService = Depends(get_file_service),
        account: Account = Depends(get_current_account)
):
    """
    Upload a file to a specific project.
    If `overwrite` is true, it replaces existing files with the same name.
    """
    return await file_service.upload_file(overwrite=overwrite,file=file,project_id=project_id)