import os

from fastapi import UploadFile, HTTPException
from datetime import datetime, timedelta, UTC
from PIL import Image
import pytesseract
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.repository.file_repository import FileRepository
from backend.schemas.file import FileCheckResponse
from backend.schemas.qdrant import QdrantPayload, PayloadStatus, UploadedFileResponse

class FileService:
    def __init__(self,file_repository: FileRepository):
        self.file_repository = file_repository

    async def convert_to_chunks(self, file: UploadFile,project_id:str) -> list[QdrantPayload]:
        if file.size and file.size > 5*1024*1024:
            raise HTTPException(status_code=400, detail="File too large.")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

        temp_file_path = f"temp_{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                buffer.write(chunk)

        try:
            file_extension = file.filename.split(".")[-1].lower() if file.filename is not None else ""

            if file_extension == "pdf":
                loader = PyPDFLoader(temp_file_path)
                documents = loader.load()

            elif file_extension in ["jpg", "jpeg", "png"]:
                extracted_text = pytesseract.image_to_string(Image.open(temp_file_path))
                doc = Document(
                    page_content=extracted_text,
                    metadata={"source": file.filename, "page": 1}
                )
                documents = [doc]

            else:
                raise HTTPException(status_code=400, detail="Unsupported file type. Please upload PDF, JPG, or PNG.")

            expiration_time = (datetime.now(UTC) + timedelta(hours=2)).isoformat()

            chunks = text_splitter.split_documents(documents)
            payload = []
            for i, chunk in enumerate(chunks):
                payload.append(QdrantPayload(
                    project_id=project_id,
                    text_chunk=chunk.page_content,
                    document_name=file.filename or f'file.{file_extension}',
                    status=PayloadStatus.PENDING,
                    last_edited=expiration_time))

            return payload

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)


    async def upload_file(self, overwrite: bool, file: UploadFile, project_id:str):
        try:
            if overwrite:
                self.file_repository.delete_file(document_name=file.filename, project_id=project_id)

            payloads = await self.convert_to_chunks(file, project_id)
            await self.file_repository.upload_to_qdrant(payloads=payloads)

            if payloads:
                return UploadedFileResponse(
                    document_name=payloads[0].document_name,
                    payloadStatus=payloads[0].status,
                )

        except Exception as e:
            raise HTTPException(status_code=500, detail="Unable to process file")


    def check_if_file_exists(self, filename: str|None, project_id: str)->FileCheckResponse:
        is_file_exist= self.file_repository.check_if_file_exists(filename=filename, project_id=project_id)
        if is_file_exist:
            return FileCheckResponse(
                exists=True,
                message=f"'{filename}' already exists. Do you want to overwrite it?"
            )

        return FileCheckResponse(exists=False, message="Ready for upload.")