# StructureIQ Build Progress

## Status: IN PROGRESS
## Last Updated: 2026-04-17T02:00:00Z
## Last Completed Step: New stream_update indexes created; waiting on provisioning
## Currently Working On: Waiting — Vertex AI index provisioning
## Next Step: When both index ops return done:true → deploy to endpoints → run ingest_standards.py → pip install → start server

## Completed Steps
- [x] GCP APIs enabled
- [x] Bucket gs://structureiq-docs created
- [x] Service account structureiq-sa created
- [x] IAM roles granted
- [x] credentials.json moved to backend/credentials.json
- [x] GCP infrastructure scripts written (enable_apis.sh, create_bucket.sh, create_service_account.sh, create_vector_indexes.sh)
- [x] .gitignore created (credentials.json listed)
- [x] .env.example created
- [x] Standards index endpoint — ID: 7384130976143638528 (us-east1, reused)
- [x] Documents index endpoint — ID: 4713496397112934400 (us-east1, reused)
- [x] Vertex AI standards index (stream_update) — ID: 5863849442557296640 (us-east1)
- [x] Vertex AI documents index (stream_update) — ID: 8407961019556560896 (us-east1)
- [x] .env updated with new stream_update index IDs

## Pending Steps
- [ ] WAIT: Vertex AI indexes still provisioning (30-60 min from ~00:06 UTC) — deploy indexes to endpoints after provisioning
- [x] Build standards JSON files (ADA, OSHA, IBC lite, ASHRAE lite)
- [x] app/ingestion/embedder.py built
- [x] scripts/ingest_standards.py built
- [ ] Run ingest_standards.py (blocked until Vertex AI indexes finish provisioning ~00:36-01:06 UTC)
- [x] Build backend core (config, pdf_parser, cost_tracker, guardrails, compliance, rag, vision)
- [x] Build API routes (health, upload, query, report, main)
- [x] requirements.txt + Dockerfile written
- [x] Build frontend (Next.js 14, TypeScript, Tailwind, shadcn/ui) — 0 TypeScript errors
- [ ] Deploy backend to Cloud Run (command below)
- [ ] Deploy frontend to Vercel

## Cloud Run Deploy Command
```bash
gcloud builds submit --tag gcr.io/structureiq/structureiq-backend

gcloud run deploy structureiq-backend \
  --image gcr.io/structureiq/structureiq-backend \
  --platform managed \
  --region us-east1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars GOOGLE_CLOUD_PROJECT=structureiq,GCS_BUCKET_NAME=structureiq-docs,VERTEX_LOCATION=us-east1,LANGCHAIN_TRACING_V2=true,LANGCHAIN_PROJECT=structureiq \
  --set-secrets GOOGLE_API_KEY=google-api-key:latest,LANGCHAIN_API_KEY=langsmith-api-key:latest
```
Notes:
- `--max-instances=10` caps concurrent instances to control cost; increase for production load
- `--timeout 300` is required for PDF parsing + multi-query report generation (can hit 60-90s)
- `--memory 2Gi` is required — PDF parsing with PyMuPDF is memory intensive, do not reduce
- Large file uploads (up to 100 MB) are handled at the app layer via BodySizeLimitMiddleware; Cloud Run's default ingress accepts up to 32 MB per request body — for production 100 MB uploads, front with a Cloud Load Balancer or upload directly to GCS via signed URL

## Vertex AI Deploy Operations (us-east1) — CURRENT

Indexes deployed to endpoints with IDs `standards_v2` / `documents_v2`. Check deploy status:

```bash
export PATH="$PATH:$HOME/Downloads/google-cloud-sdk/bin"

# Standards deploy → endpoint 7384130976143638528
gcloud ai operations describe 3685175467175837696 \
  --index-endpoint=7384130976143638528 \
  --region=us-east1 --project=structureiq

# Documents deploy → endpoint 4713496397112934400
gcloud ai operations describe 8491642169486999552 \
  --index-endpoint=4713496397112934400 \
  --region=us-east1 --project=structureiq
```

When both return `"done": true` with no error field → run `python scripts/ingest_standards.py`.

## Blockers
- Vertex AI index deploy operations must complete before ingest_standards.py will work
- Cloud Run has a 32 MB default request body limit — 100 MB uploads require a Cloud Load Balancer or direct-to-GCS signed URL flow for production (current app middleware enforces the limit but payloads may be rejected at the Cloud Run ingress layer before reaching the app)

## Future State & Vision

See [ROADMAP.md](./ROADMAP.md) for the full product roadmap.

**v1.1 — Immediate Post-MVP:** Signed URL uploads (bypass Cloud Run 32 MB limit), Google OAuth, document history per user.

**v2.0 — Short Term:** Real-time collaboration, custom standards upload, webhook notifications, API access for third-party integrations.

**v3.0 — Long Term:** Computer vision on job site photos (OSHA auto-detection), Procore/Autodesk/Bluebeam integrations, continuous monitoring when standards update, multi-language support, mobile app for field inspectors.

---

## Known Gotchas

- **CRITICAL — stream_update required:** Vertex AI Vector Search indexes MUST be created with `--index-update-method=stream_update`. Using `batch_update` (the default) makes `upsert_datapoints()` silently fail or error — real-time document ingestion breaks entirely. Always verify with `gcloud ai indexes describe <ID> --region=us-east1` and confirm `indexUpdateMethod: STREAM_UPDATE` before deploying.
- **Cloud Run 32 MB ingress limit:** Cloud Run rejects request bodies over 32 MB before they reach the app. The `BodySizeLimitMiddleware` in `main.py` handles the app-level 100 MB check, but for true large-file support use GCS signed URLs (v1.1 roadmap item).
- **Index provisioning time:** New indexes take 30–60 min to provision even when empty. Deploy-to-endpoint operations take another 15–30 min after that. Plan accordingly — do not assume an index is ready just because the create command returned.

## Notes
- gcloud is at ~/Downloads/google-cloud-sdk/bin
- GCP project: structureiq, number: 381539677677
- Bucket gs://structureiq-docs already created
- Service account: structureiq-sa@structureiq.iam.gserviceaccount.com
- credentials.json is at backend/credentials.json (gitignored)
- Region: us-east1 (updated from us-central1)
