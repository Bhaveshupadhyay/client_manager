from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.api.dependencies import get_current_account, get_file_service
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
    is_file_exist = file_service.check_if_file_exists(filename=filename, project_id=project_id)

    if is_file_exist:
        return FileCheckResponse(
            exists=True,
            message=f"'{filename}' already exists. Do you want to overwrite it?"
        )

    return FileCheckResponse(exists=False, message="Ready for upload.")


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
    if overwrite:
        file_service.delete_file(document_name=file.filename, project_id=project_id)

    payloads= await file_service.convert_to_chunks(file=file,project_id=project_id)
    await file_service.upload_to_qdrant(payloads=payloads)
    if payloads:
        return UploadedFileResponse(
            document_name=payloads[0].document_name,
            payloadStatus=payloads[0].status,
        )

    raise HTTPException(status_code=500, detail="Unable to process file")