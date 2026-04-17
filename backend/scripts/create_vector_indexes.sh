#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="structureiq"
REGION="us-east1"
DIMENSIONS=768  # text-embedding-004 output dimension

# CRITICAL: must be stream_update for live upsert. batch_update breaks real-time document ingestion.
echo "Creating Vertex AI Vector Search index: structureiq-standards..."
STANDARDS_INDEX=$(gcloud ai indexes create \
  --display-name="structureiq-standards" \
  --description="AEC compliance standards knowledge base" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --metadata-schema-uri="gs://google-cloud-aiplatform/schema/matchingengine/metadata/nearest_neighbor_search_1.0.0.yaml" \
  --index-update-method="stream_update" \
  --format="value(name)" 2>&1)

echo "Standards index created: ${STANDARDS_INDEX}"
STANDARDS_INDEX_ID=$(echo "${STANDARDS_INDEX}" | awk -F'/' '{print $NF}')
echo "Standards Index ID: ${STANDARDS_INDEX_ID}"

echo ""
# CRITICAL: must be stream_update for live upsert. batch_update breaks real-time document ingestion.
echo "Creating Vertex AI Vector Search index: structureiq-documents..."
DOCUMENTS_INDEX=$(gcloud ai indexes create \
  --display-name="structureiq-documents" \
  --description="User uploaded construction documents" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --metadata-schema-uri="gs://google-cloud-aiplatform/schema/matchingengine/metadata/nearest_neighbor_search_1.0.0.yaml" \
  --index-update-method="stream_update" \
  --format="value(name)" 2>&1)

echo "Documents index created: ${DOCUMENTS_INDEX}"
DOCUMENTS_INDEX_ID=$(echo "${DOCUMENTS_INDEX}" | awk -F'/' '{print $NF}')
echo "Documents Index ID: ${DOCUMENTS_INDEX_ID}"

echo ""
echo "Creating index endpoints..."

STANDARDS_ENDPOINT=$(gcloud ai index-endpoints create \
  --display-name="structureiq-standards-endpoint" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --format="value(name)" 2>&1)
STANDARDS_ENDPOINT_ID=$(echo "${STANDARDS_ENDPOINT}" | awk -F'/' '{print $NF}')
echo "Standards endpoint ID: ${STANDARDS_ENDPOINT_ID}"

DOCUMENTS_ENDPOINT=$(gcloud ai index-endpoints create \
  --display-name="structureiq-documents-endpoint" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --format="value(name)" 2>&1)
DOCUMENTS_ENDPOINT_ID=$(echo "${DOCUMENTS_ENDPOINT}" | awk -F'/' '{print $NF}')
echo "Documents endpoint ID: ${DOCUMENTS_ENDPOINT_ID}"

echo ""
echo "Deploying standards index to endpoint (this may take 15-30 minutes)..."
gcloud ai index-endpoints deploy-index "${STANDARDS_ENDPOINT_ID}" \
  --deployed-index-id="standards_deployed" \
  --display-name="Standards Deployed Index" \
  --index="${STANDARDS_INDEX_ID}" \
  --region="${REGION}" \
  --project="${PROJECT_ID}"

echo ""
echo "Deploying documents index to endpoint (this may take 15-30 minutes)..."
gcloud ai index-endpoints deploy-index "${DOCUMENTS_ENDPOINT_ID}" \
  --deployed-index-id="documents_deployed" \
  --display-name="Documents Deployed Index" \
  --index="${DOCUMENTS_INDEX_ID}" \
  --region="${REGION}" \
  --project="${PROJECT_ID}"

echo ""
echo "============================================"
echo "ADD THESE TO YOUR .env FILE:"
echo "VERTEX_STANDARDS_INDEX_ID=${STANDARDS_INDEX_ID}"
echo "VERTEX_DOCUMENTS_INDEX_ID=${DOCUMENTS_INDEX_ID}"
echo "VERTEX_STANDARDS_INDEX_ENDPOINT=${STANDARDS_ENDPOINT_ID}"
echo "VERTEX_DOCUMENTS_INDEX_ENDPOINT=${DOCUMENTS_ENDPOINT_ID}"
echo "============================================"
