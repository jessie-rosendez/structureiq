"""
PDF text + image extraction with page-aware chunking.
"""

import io
from pathlib import Path
from typing import Any

import pdfplumber
import fitz  # PyMuPDF


def extract_text_chunks(
    pdf_bytes: bytes,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list[dict[str, Any]]:
    """
    Extract text from PDF and split into overlapping chunks.

    Returns list of dicts: {text, page, chunk_index, char_start}.
    """
    chunks: list[dict[str, Any]] = []
    full_pages: list[dict[str, Any]] = []

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                full_pages.append({"page": page_num, "text": text})

    # Chunk each page's text with overlap
    chunk_idx = 0
    for page_data in full_pages:
        text = page_data["text"]
        page_num = page_data["page"]
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            if chunk_text.strip():
                chunks.append(
                    {
                        "text": chunk_text,
                        "page": page_num,
                        "chunk_index": chunk_idx,
                        "char_start": start,
                    }
                )
                chunk_idx += 1
            start += chunk_size - chunk_overlap

    return chunks


def extract_images(pdf_bytes: bytes) -> list[dict[str, Any]]:
    """
    Extract embedded images from PDF using PyMuPDF.

    Returns list of dicts: {page, image_index, image_bytes, ext}.
    """
    images: list[dict[str, Any]] = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        image_list = page.get_images(full=True)
        for img_idx, img_info in enumerate(image_list):
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            images.append(
                {
                    "page": page_num + 1,
                    "image_index": img_idx,
                    "image_bytes": base_image["image"],
                    "ext": base_image["ext"],
                    "mime_type": f"image/{base_image['ext']}",
                }
            )

    doc.close()
    return images


def get_pdf_metadata(pdf_bytes: bytes) -> dict[str, Any]:
    """Extract basic PDF metadata."""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        meta = pdf.metadata or {}
        return {
            "page_count": len(pdf.pages),
            "title": meta.get("Title", ""),
            "author": meta.get("Author", ""),
            "creator": meta.get("Creator", ""),
        }
