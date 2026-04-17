#!/usr/bin/env bash
set -euo pipefail

echo "Setting project to structureiq..."
gcloud config set project structureiq

echo "Enabling required GCP APIs..."
gcloud services enable \
  aiplatform.googleapis.com \
  storage.googleapis.com \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  containerregistry.googleapis.com \
  discoveryengine.googleapis.com \
  secretmanager.googleapis.com

echo "All APIs enabled successfully."
