from abc import ABC, abstractmethod

from fastembed import SparseTextEmbedding, TextEmbedding
from fastembed.common.model_description import PoolingType, ModelSource

from backend.schemas.qdrant import SparseModelResponse

class EmbeddingsProvider(ABC):
    @abstractmethod
    def generate_dense_embeddings(self, text: list[str]):
        pass

    @abstractmethod
    def generate_sparse_embeddings(self, text: list[str]):
        pass


class FastEmbeddingProvider(EmbeddingsProvider):
    def __init__(self):
        TextEmbedding.add_custom_model(
            model="intfloat/multilingual-e5-small",
            pooling=PoolingType.MEAN,
            normalization=True,
            sources=ModelSource(hf="intfloat/multilingual-e5-small"),
            dim=384,
            model_file="onnx/model.onnx"
        )
        self.dense_model = TextEmbedding(model_name="intfloat/multilingual-e5-small")
        self.sparse_model = SparseTextEmbedding(model_name="prithvida/Splade_PP_en_v1")


    def generate_dense_embeddings(self, text: list[str])-> list[list[float]]:
        try:
            return [dense_embedding.tolist() for dense_embedding in self.dense_model.embed(text)]
        except Exception as e:
            raise e

    def generate_sparse_embeddings(self, text: list[str])->list[SparseModelResponse]:
        try:
            generator = self.sparse_model.embed(text)

            return [
                SparseModelResponse(indices=sparse.indices.tolist(), values=sparse.values.tolist())
                for sparse in generator
            ]
        except Exception as e:
            raise e