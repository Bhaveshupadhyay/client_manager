import os

from fastapi import UploadFile, HTTPException
from datetime import datetime, timedelta, UTC
from PIL import Image
import pytesseract
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct

from backend.services.llm_provider import LLmProvider


class FileService:
    def __init__(self,qdrant_client:QdrantClient,llm_provider:LLmProvider):
        self.qdrant_client = qdrant_client
        self.llm_provider = llm_provider

    # def confirm_file_attachment(COLLECTION_NAME: str, file_id: str):
    # Tell Qdrant: Update all vectors with this file_id to status="active"
    #     client.set_payload(
    #         collection_name=COLLECTION_NAME,
    #         payload={"status": "active"}, # Overwrites 'pending'
    #         points_selector=models.Filter(
    #             must=[models.FieldCondition(key="file_id", match=models.MatchValue(value=file_id))]
    #         )
    #     )

    async def convert_to_chunks(self, file: UploadFile):
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

            expiration_time = datetime.now(UTC) + timedelta(hours=2)

            chunks = text_splitter.split_documents(documents)
            response_data = []
            for i, chunk in enumerate(chunks):
                response_data.append({
                    "chunk_id": i + 1,
                    "content": chunk.page_content,
                    "metadata": chunk.metadata
                })
            payload = {
                "file_id": temp_file_path,
                "text": response_data,
                "status": "pending",
                "expires_at": expiration_time.timestamp()
            }

            return {
                "message": "Successfully processed and chunked.",
                "total_chunks": len(response_data),
                "chunks": response_data
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)


    async def upload_to_qdrant(self, text:str, document_name:str, project_id:str):

        embedding = await self.llm_provider.generate_embeddings(text) or []
        new_payload = {
            "project_id": project_id,
            "document_name": document_name,
            "status": "active",
            "last_edited": "2026-07-04T12:00:00Z"
        }
        self.qdrant_client.upsert(
            collection_name="client_conversations",
            points=[
                PointStruct(
                    id=1,
                    vector=embedding,
                    payload=new_payload
                )
            ]
        )