from abc import ABC, abstractmethod

import httpx
import requests
from fastembed import SparseTextEmbedding
from google import genai
from google.genai import types

from backend.core.config import config
from backend.schemas.qdrant import SparseModelResponse

class DenseEmbeddingsProvider(ABC):

    @abstractmethod
    def generate_dense_embeddings(self, text: list[str]):
        pass

class SparseEmbeddingsProvider(ABC):

    @abstractmethod
    async def generate_sparse_embeddings(self, text: list[str]):
        pass


class FastEmbeddingProviderSparse(SparseEmbeddingsProvider):
    def __init__(self):
        self.sparse_model = SparseTextEmbedding(model_name="prithvida/Splade_PP_en_v1")


    async def generate_sparse_embeddings(self, text: list[str])->list[SparseModelResponse]:
        try:
            generator = self.sparse_model.embed(text)

            return [
                SparseModelResponse(indices=sparse.indices.tolist(), values=sparse.values.tolist())
                for sparse in generator
            ]
        except Exception as e:
            raise e

class HuggingFaceProviderSparse(SparseEmbeddingsProvider):
    def __init__(self):
        self.url= f"https://{config.HUGGING_FACE_USER_NAME}-{config.HUGGING_FACE_SPACE}.hf.space/generate_sparse"


    async def generate_sparse_embeddings(self, text: list[str])->list[SparseModelResponse]:
        try:
            headers = {
                "Authorization": f"Bearer {config.HUGGING_FACE_TOKEN}",
                "Content-Type": "application/json"
            }
            payload = {
                "chunks": text
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(self.url, json=payload, headers=headers, timeout=30.0)
                response.raise_for_status()
                embeddings = response.json()['embeddings']

            return [
                SparseModelResponse.model_validate(sparse)
                for sparse in embeddings
            ]
        except Exception as e:
            raise e

class GeminiDenseEmbeddingsProvider(DenseEmbeddingsProvider):
    def __init__(self):
        self.client = genai.Client()

    def generate_dense_embeddings(self, text: list[str])-> list[list[float]]:
        try:
            contents = [
                types.Content(parts=[types.Part.from_text(text=chunk)])
                for chunk in text
            ]
            response = self.client.models.embed_content(
                model='gemini-embedding-2',
                contents=contents,
                config=types.EmbedContentConfig(output_dimensionality=384)
            )

            if response.embeddings is None:
                raise ValueError("Gemini API returned a null embedding for a text chunk.")

            vectors: list[list[float]] = []

            for embedding in response.embeddings:
                if embedding.values is None:
                    raise ValueError("Gemini API returned a null embedding for a text chunk.")

                vectors.append(embedding.values)

            return vectors
        except Exception as e:
            raise e