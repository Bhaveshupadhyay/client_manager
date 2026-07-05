import logging

from fastembed import TextEmbedding, SparseTextEmbedding
from fastembed.common.model_description import PoolingType, ModelSource

logger = logging.getLogger(__name__)
def warmup():
    logger.info("Pre-downloading models into Docker image layers...")
    TextEmbedding.add_custom_model(
        model="intfloat/multilingual-e5-small",
        pooling=PoolingType.MEAN,
        normalization=True,
        sources=ModelSource(hf="intfloat/multilingual-e5-small"),
        dim=384,
        model_file="onnx/model.onnx"
    )
    TextEmbedding(model_name="intfloat/multilingual-e5-small")
    SparseTextEmbedding(model_name="prithvida/Splade_PP_en_v1")
    logger.info("Models downloaded successfully!")

if __name__ == "__main__":
    warmup()