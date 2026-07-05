import logging

from fastembed import SparseTextEmbedding

logger = logging.getLogger(__name__)
def warmup():
    logger.info("Pre-downloading models into Docker image layers...")
    SparseTextEmbedding(model_name="prithvida/Splade_PP_en_v1")
    logger.info("Models downloaded successfully!")

if __name__ == "__main__":
    warmup()