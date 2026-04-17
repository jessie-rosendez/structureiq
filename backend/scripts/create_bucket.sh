#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="structureiq"
BUCKET_NAME="structureiq-docs"
REGION="us-east1"

echo "Creating GCS bucket: gs://${BUCKET_NAME}..."
gsutil mb -p "${PROJECT_ID}" -c STANDARD -l "${REGION}" "gs://${BUCKET_NAME}"

echo "Enabling uniform bucket-level access..."
gsutil uniformbucketlevelaccess set on "gs://${BUCKET_NAME}"

echo "Bucket gs://${BUCKET_NAME} created and configured."
