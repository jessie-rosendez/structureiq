import os
import time
from typing import List
from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel
import vertexai


def init_vertex(project: str, location: str) -> None:
    vertexai.init(project=project, location=location)


def embed_texts(texts: List[str], batch_size: int = 5) -> List[List[float]]:
    """Embed a list of texts using Vertex AI text-embedding-004.

    Batches requests to avoid rate limits. Returns list of 768-dim vectors.
    """
    model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    all_embeddings: List[List[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        embeddings = model.get_embeddings(batch)
        all_embeddings.extend([e.values for e in embeddings])
        if i + batch_size < len(texts):
            time.sleep(0.5)  # avoid quota exhaustion

    return all_embeddings


def embed_single(text: str) -> List[float]:
    model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    result = model.get_embeddings([text])
    return result[0].values
