import os
import uuid

from fastapi import UploadFile, HTTPException
from datetime import datetime, timedelta, UTC, timezone
from PIL import Image
import pytesseract
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import PointStruct

from backend.schemas.qdrant import QdrantPayload, PayloadStatus
from backend.services.embeddings_provider import EmbeddingsProvider

COLLECTION_NAME= 'client_conversations'

class FileService:
    def __init__(self,qdrant_client:QdrantClient,embeddings_provider:EmbeddingsProvider):
        self.qdrant_client = qdrant_client
        self.embeddings_provider = embeddings_provider

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


    async def upload_to_qdrant(self, payloads:list[QdrantPayload]):

        try:

            chunks= [payload.text_chunk for payload in payloads]
            dense_embeddings =  self.embeddings_provider.generate_dense_embeddings(chunks)
            sparse_embeddings =  self.embeddings_provider.generate_sparse_embeddings(chunks)

            points_to_upsert = []

            for i, payload in enumerate(payloads):
                point_id = str(uuid.uuid4())

                single_sparse = models.SparseVector(
                    indices=sparse_embeddings[i].indices,
                    values=sparse_embeddings[i].values
                )
                points_to_upsert.append(
                    PointStruct(
                        id=point_id,
                        vector={
                            "dense": dense_embeddings[i],
                            "sparse": single_sparse
                        },
                        payload=payload.model_dump()
                    )
                )


            self.qdrant_client.upsert(
                collection_name=COLLECTION_NAME,
                points=points_to_upsert
            )
        except Exception as e:
            raise e


    async def update_document_status_to_active(self, document_name: str, project_id: str):

        try:
            self.qdrant_client.set_payload(
                collection_name=COLLECTION_NAME,
                payload={
                    "status": PayloadStatus.ACTIVE.value,
                    "last_edited": datetime.now(timezone.utc).isoformat()
                },
                points=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_name",
                            match=models.MatchValue(value=document_name)
                        ),
                        models.FieldCondition(
                            key="project_id",
                            match=models.MatchValue(value=project_id)
                        )
                    ]
                )
            )

        except Exception as e:
            raise e


    def check_if_file_exists(self, filename: str|None, project_id: str)->bool:
        if filename is None:
            return False
        try:
            file, _ = self.qdrant_client.scroll(
                collection_name=COLLECTION_NAME,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_name",
                            match=models.MatchValue(value=filename),
                        ),
                        models.FieldCondition(
                            key="project_id",
                            match=models.MatchValue(value=project_id),
                        )
                    ]
                ),
                limit=1,
                with_payload=False,
                with_vectors=False
            )

            return True if file else False

        except Exception as e:
            raise e

    def delete_file(self, document_name: str|None, project_id: str):
        if document_name is None:
            raise ValueError("document name cannot be None")
        try:
            self.qdrant_client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_name",
                            match=models.MatchValue(value=document_name)
                        ),
                        models.FieldCondition(
                            key="project_id",
                            match=models.MatchValue(value=project_id)
                        )
                    ]
                )
            )

        except Exception as e:
            raise e