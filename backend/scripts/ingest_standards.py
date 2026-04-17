#!/usr/bin/env python3
"""
One-time script: ingest AEC standards JSON files into Vertex AI Vector Search.

Run: python scripts/ingest_standards.py
Requires: backend/.env with VERTEX_STANDARDS_INDEX_ID and GOOGLE_CLOUD_PROJECT set.
"""

import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Resolve paths relative to the backend/ directory
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))
load_dotenv(BACKEND_DIR / ".env")

import vertexai
from google.cloud import aiplatform
from app.ingestion.embedder import embed_texts, init_vertex

PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
LOCATION = os.environ.get("VERTEX_LOCATION", "us-east1")
STANDARDS_INDEX_ID = os.environ["VERTEX_STANDARDS_INDEX_ID"]
STANDARDS_DIR = BACKEND_DIR / "app" / "data" / "standards"

GEMINI_INPUT_COST_PER_M = 0.00002  # text-embedding-004 is effectively free but track calls


def section_to_text(standard_name: str, section: dict[str, Any]) -> str:
    """Convert a standards section dict to an embeddable text string."""
    parts = [
        f"Standard: {standard_name}",
        f"Section: {section['section_id']} — {section['title']}",
        f"Category: {section.get('category', '')}",
        f"Requirement: {section['requirement']}",
        f"Keywords: {', '.join(section.get('keywords', []))}",
        f"Applies to: {', '.join(section.get('applies_to', []))}",
        f"Severity: {section.get('severity', '')}",
    ]
    if "climate_zone_values" in section:
        cz = section["climate_zone_values"]
        parts.append("Climate zone values: " + "; ".join(f"CZ{k}: {v}" for k, v in cz.items()))
    if "representative_values" in section:
        rv = section["representative_values"]
        parts.append("Representative values: " + "; ".join(f"{k}: {v}" for k, v in rv.items()))
    return "\n".join(parts)


def load_all_sections() -> list[dict[str, Any]]:
    """Load every section from every standards JSON file."""
    records = []
    for json_file in sorted(STANDARDS_DIR.glob("*.json")):
        print(f"Loading {json_file.name}...")
        with open(json_file) as f:
            data = json.load(f)
        standard_name = data["standard"]
        version = data.get("version", "")
        for section in data["sections"]:
            text = section_to_text(standard_name, section)
            records.append(
                {
                    "id": f"{json_file.stem}__{section['section_id'].replace('.', '_').replace('-', '_')}",
                    "text": text,
                    "metadata": {
                        "standard": standard_name,
                        "version": version,
                        "section_id": section["section_id"],
                        "title": section["title"],
                        "category": section.get("category", ""),
                        "severity": section.get("severity", ""),
                        "source_file": json_file.name,
                    },
                }
            )
    return records


def upsert_to_index(index_resource_name: str, datapoints: list[dict[str, Any]]) -> None:
    """Upsert embedded datapoints into Vertex AI Vector Search index."""
    from google.cloud.aiplatform_v1.types import IndexDatapoint
    from google.cloud import aiplatform

    index = aiplatform.MatchingEngineIndex(index_name=index_resource_name)

    batch_size = 100
    for i in range(0, len(datapoints), batch_size):
        batch = datapoints[i : i + batch_size]
        index_datapoints = [
            IndexDatapoint(
                datapoint_id=dp["id"],
                feature_vector=dp["embedding"],
                restricts=[
                    IndexDatapoint.Restriction(
                        namespace="standard",
                        allow_list=[dp["metadata"]["standard"][:50]],
                    ),
                    IndexDatapoint.Restriction(
                        namespace="category",
                        allow_list=[dp["metadata"]["category"][:50]],
                    ),
                ],
            )
            for dp in batch
        ]
        index.upsert_datapoints(datapoints=index_datapoints)
        print(f"  Upserted batch {i // batch_size + 1} ({len(batch)} datapoints)")
        time.sleep(0.2)


def main() -> None:
    print(f"Initializing Vertex AI — project={PROJECT}, location={LOCATION}")
    init_vertex(PROJECT, LOCATION)

    index_resource_name = (
        f"projects/{PROJECT}/locations/{LOCATION}/indexes/{STANDARDS_INDEX_ID}"
    )
    print(f"Target index: {index_resource_name}")

    print("\nLoading standards sections...")
    records = load_all_sections()
    print(f"Total sections loaded: {len(records)}")

    print("\nEmbedding sections (text-embedding-004)...")
    texts = [r["text"] for r in records]
    embeddings = embed_texts(texts, batch_size=5)
    print(f"Embeddings generated: {len(embeddings)}, dimensions: {len(embeddings[0])}")

    for record, embedding in zip(records, embeddings):
        record["embedding"] = embedding

    print("\nUpserting to Vertex AI Vector Search...")
    upsert_to_index(index_resource_name, records)

    print(f"\nDone. {len(records)} standards sections ingested into index {STANDARDS_INDEX_ID}.")
    print("Estimated embedding cost: $0.00 (text-embedding-004 is free tier for this volume)")

    # Write a manifest for traceability
    manifest_path = BACKEND_DIR / "app" / "data" / "standards" / "ingestion_manifest.json"
    manifest = {
        "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "index_id": STANDARDS_INDEX_ID,
        "total_sections": len(records),
        "files": [
            {
                "file": r["metadata"]["source_file"],
                "section_id": r["metadata"]["section_id"],
                "id": r["id"],
            }
            for r in records
        ],
    }
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Manifest written to {manifest_path}")


if __name__ == "__main__":
    main()
