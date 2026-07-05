import uuid
from datetime import datetime, timezone

from qdrant_client import QdrantClient, models
from qdrant_client.http.models import PointStruct

from backend.schemas.qdrant import QdrantPayload, PayloadStatus
from backend.services.embeddings_provider import EmbeddingsProvider


class FileRepository:
    def __init__(self, qdrant_client: QdrantClient, embeddings_provider: EmbeddingsProvider, collection_name: str):
        self.qdrant_client = qdrant_client
        self.embeddings_provider = embeddings_provider
        self.collection_name = collection_name

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
                collection_name=self.collection_name,
                points=points_to_upsert
            )
        except Exception as e:
            raise e


    async def update_document_status_to_active(self, document_name: str, project_id: str):

        try:
            self.qdrant_client.set_payload(
                collection_name=self.collection_name,
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
                collection_name=self.collection_name,
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
                collection_name=self.collection_name,
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