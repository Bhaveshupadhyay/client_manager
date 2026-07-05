from enum import StrEnum

from pydantic import BaseModel

class QdrantUpload(BaseModel):
    content: str
    payload: QdrantPayload


class QdrantPayload(BaseModel):
    project_id: str
    document_name: str
    text_chunk: str
    status: PayloadStatus
    last_edited: str


class PayloadStatus(StrEnum):
    """ Qdrant Payload Status """
    PENDING = 'PENDING'
    ACTIVE = 'ACTIVE'


class UploadedFileResponse(BaseModel):
    document_name: str
    payloadStatus: PayloadStatus


class SparseModelResponse(BaseModel):
    indices:list[int]
    values:list[float]


class QdrantVector(BaseModel):
    dense: list[list[float]]
    sparse: list[SparseModelResponse]
