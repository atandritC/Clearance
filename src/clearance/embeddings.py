from functools import lru_cache
from pathlib import Path
from tempfile import gettempdir

from fastembed import TextEmbedding
from clearance.config import settings


@lru_cache(maxsize=1)
def get_embedding_model() -> TextEmbedding:
    cache_dir = Path(gettempdir()) / "clearance-fastembed-cache"
    return TextEmbedding(
        model_name=settings.embedding_model,
        cache_dir=str(cache_dir),
    )


def embed_texts(texts: list[str]) -> list[list[float]]:
    return [vector.tolist() for vector in get_embedding_model().embed(texts)]
