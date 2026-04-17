#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="structureiq"
SA_NAME="structureiq-sa"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "Creating service account: ${SA_NAME}..."
gcloud iam service-accounts create "${SA_NAME}" \
  --display-name="StructureIQ Service Account" \
  --project="${PROJECT_ID}"

echo "Granting Vertex AI user role..."
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/aiplatform.user"

echo "Granting Storage objectAdmin role..."
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.objectAdmin"

echo "Granting Secret Manager accessor role..."
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/secretmanager.secretAccessor"

echo "Creating credentials key file..."
gcloud iam service-accounts keys create backend/credentials.json \
  --iam-account="${SA_EMAIL}"

echo ""
echo "IMPORTANT: credentials.json has been created in backend/."
echo "Ensure it is listed in .gitignore before any git operations."
echo "Service account setup complete."
