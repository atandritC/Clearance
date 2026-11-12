import logging
import os
from functools import lru_cache
from pathlib import Path

_CACHE_ROOT = Path("/tmp/clearance-fastembed-cache")
_HF_CACHE_ROOT = Path("/tmp/clearance-huggingface-cache")

os.environ["FASTEMBED_CACHE_PATH"] = str(_CACHE_ROOT)
os.environ["HF_HOME"] = str(_HF_CACHE_ROOT)
os.environ["HF_HUB_CACHE"] = str(_HF_CACHE_ROOT / "hub")
os.environ["HF_XET_CACHE"] = str(_HF_CACHE_ROOT / "xet")

from fastembed import TextEmbedding
from clearance.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_embedding_model() -> TextEmbedding:
    _CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    logger.info("Loading FastEmbed model with cache at %s", _CACHE_ROOT)
    return TextEmbedding(
        model_name=settings.embedding_model,
        cache_dir=str(_CACHE_ROOT),
    )


def embed_texts(texts: list[str]) -> list[list[float]]:
    return [vector.tolist() for vector in get_embedding_model().embed(texts)]
