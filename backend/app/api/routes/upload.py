"""
Document upload → GCS → parse → embed → Vertex AI documents index.
"""

import uuid
import time
from typing import Any

from fastapi import APIRouter, UploadFile, File, HTTPException
from google.cloud import storage

from app.core.config import get_settings
from app.ingestion.pdf_parser import extract_text_chunks, get_pdf_metadata
from app.ingestion.embedder import embed_texts, init_vertex
from app.models.document import UploadResponse

router = APIRouter()

# In-memory document registry: document_id → {filename, metadata, chunks}
_document_registry: dict[str, dict[str, Any]] = {}

ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
}


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    settings = get_settings()

    content_type = file.content_type or ""
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type: {content_type}. Accepted: PDF, PNG, JPG.",
        )

    file_bytes = await file.read()
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > settings.max_file_size_mb:
        raise HTTPException(
            status_code=422,
            detail=f"File size {size_mb:.1f} MB exceeds maximum {settings.max_file_size_mb} MB.",
        )

    document_id = str(uuid.uuid4())
    original_filename = file.filename or "upload"
    ext = ALLOWED_MIME_TYPES[content_type]
    gcs_blob_name = f"uploads/{document_id}{ext}"

    # Upload to GCS
    try:
        gcs_client = storage.Client(project=settings.google_cloud_project)
        bucket = gcs_client.bucket(settings.gcs_bucket_name)
        blob = bucket.blob(gcs_blob_name)
        blob.upload_from_string(file_bytes, content_type=content_type)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=(
                "Storage upload failed. Check GCS permissions, service-account credentials, "
                f"and backend configuration. Underlying error: {e}"
            ),
        )

    if content_type != "application/pdf":
        # Image upload — no text chunking, store reference for vision
        _document_registry[document_id] = {
            "filename": original_filename,
            "gcs_path": gcs_blob_name,
            "type": "image",
            "mime_type": content_type,
            "chunks": [],
            "chunk_count": 0,
        }
        return UploadResponse(
            document_id=document_id,
            filename=original_filename,
            page_count=1,
            chunks_indexed=0,
            message="Image uploaded. Use /query with vision mode.",
        )

    # PDF — extract, chunk, embed, upsert
    try:
        metadata = get_pdf_metadata(file_bytes)
        chunks = extract_text_chunks(
            file_bytes,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"PDF parse failed: {e}")

    if not chunks:
        raise HTTPException(status_code=422, detail="No extractable text found in PDF.")

    try:
        init_vertex(settings.google_cloud_project, settings.vertex_location)
        texts = [c["text"] for c in chunks]
        embeddings = embed_texts(texts, batch_size=5)

        # Upsert to documents index
        _upsert_document_chunks(document_id, chunks, embeddings, settings)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=(
                "Document indexing failed. Check Vertex AI permissions, index deployment, "
                f"and backend configuration. Underlying error: {e}"
            ),
        )

    # Cache chunks for fast lookup in this session
    _document_registry[document_id] = {
        "filename": original_filename,
        "gcs_path": gcs_blob_name,
        "type": "pdf",
        "metadata": metadata,
        "chunks": chunks,
        "embeddings": embeddings,
        "chunk_count": len(chunks),
    }

    return UploadResponse(
        document_id=document_id,
        filename=original_filename,
        page_count=metadata["page_count"],
        chunks_indexed=len(chunks),
        message=f"Document indexed successfully. {len(chunks)} chunks ready for queries.",
    )


def _upsert_document_chunks(
    document_id: str,
    chunks: list[dict[str, Any]],
    embeddings: list[list[float]],
    settings: Any,
) -> None:
    from google.cloud.aiplatform_v1.types import IndexDatapoint
    from google.cloud import aiplatform

    index = aiplatform.MatchingEngineIndex(
        index_name=settings.documents_index_resource_name
    )

    datapoints = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        dp = IndexDatapoint(
            datapoint_id=f"{document_id}__chunk_{i}",
            feature_vector=embedding,
            restricts=[
                IndexDatapoint.Restriction(namespace="document_id", allow_list=[document_id]),
                IndexDatapoint.Restriction(namespace="page", allow_list=[str(chunk["page"])]),
            ],
        )
        datapoints.append(dp)

    # Batch upsert in groups of 100
    for i in range(0, len(datapoints), 100):
        index.upsert_datapoints(datapoints=datapoints[i : i + 100])
        time.sleep(0.1)


def get_document(document_id: str) -> dict[str, Any] | None:
    return _document_registry.get(document_id)
