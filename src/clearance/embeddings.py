from functools import lru_cache

from fastembed import TextEmbedding
from clearance.config import settings


@lru_cache(maxsize=1)
def get_embedding_model() -> TextEmbedding:
    return TextEmbedding(
        model_name=settings.embedding_model,
        cache_dir="/tmp/clearance-fastembed-cache",
    )


def embed_texts(texts: list[str]) -> list[list[float]]:
    return [vector.tolist() for vector in get_embedding_model().embed(texts)]
