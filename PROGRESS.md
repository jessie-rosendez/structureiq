# StructureIQ Build Progress

## Status: LIVE IN PRODUCTION
## Last Updated: 2026-04-17T07:10:00Z
## Current State: End-to-end working — upload → query → full compliance report on production URLs

---

## Live URLs

| Service | URL |
|---|---|
| Frontend | https://frontend-phi-five-58.vercel.app |
| Backend | https://structureiq-backend-eyyi6tggvq-ue.a.run.app |
| Health check | `curl https://structureiq-backend-eyyi6tggvq-ue.a.run.app/health` |

---

## Completed Steps

- [x] GCP APIs enabled
- [x] Bucket `gs://structureiq-docs` created
- [x] Service account `structureiq-sa@structureiq.iam.gserviceaccount.com` created with all required IAM roles
- [x] `credentials.json` gitignored, excluded from Docker image via `.dockerignore`
- [x] GCP infrastructure scripts written (`enable_apis.sh`, `create_bucket.sh`, `create_service_account.sh`, `create_vector_indexes.sh`)
- [x] Vertex AI standards index (stream_update) — ID: `5863849442557296640` (us-east1)
- [x] Vertex AI documents index (stream_update) — ID: `8407961019556560896` (us-east1)
- [x] Standards index endpoint — ID: `7384130976143638528` (us-east1), deployed index: `standards_v2`
- [x] Documents index endpoint — ID: `4713496397112934400` (us-east1), deployed index: `documents_v2`
- [x] Standards KB ingested (`scripts/ingest_standards.py`) — ADA, OSHA 1926, IBC 2021, ASHRAE 90.1
- [x] Backend core built (config, pdf_parser, cost_tracker, guardrails, compliance, rag, vision)
- [x] API routes built (health, upload, query, report)
- [x] `requirements.txt` + `Dockerfile` written
- [x] Frontend built (Next.js 14, TypeScript, Tailwind) — upload, query, report pages
- [x] Cloud Build trigger (`structureiq-main-deploy`) — auto-deploys backend on every push to `main`
- [x] Backend deployed to Cloud Run — auto-deployed via Cloud Build on every push to `main` (check current revision in GCP console)
- [x] Frontend deployed to Vercel — `frontend-phi-five-58.vercel.app`
- [x] `NEXT_PUBLIC_API_URL` set in Vercel dashboard and baked into production build
- [x] End-to-end verified in production: upload PDF → query → full 10-standard compliance report

---

## Architecture

- **Two-layer RAG:** Vertex AI Vector Search (document chunks + standards KB) → Gemini synthesis
- **Model:** `gemini-2.5-flash` via `google-genai` SDK with `vertexai=True`, location `global`
- **Embedding:** `text-embedding-004` via Vertex AI
- **Storage:** GCS `structureiq-docs` bucket for uploaded PDFs
- **Auth on Cloud Run:** ADC via attached `structureiq-sa` service account (no credentials file needed)
- **Secrets:** `GOOGLE_API_KEY`, `LANGCHAIN_API_KEY` via GCP Secret Manager

---

## Deployment Flow

Every `git push origin main` auto-triggers Cloud Build → builds Docker image tagged with `$COMMIT_SHA` → pushes to `gcr.io/structureiq/structureiq-backend` → deploys to Cloud Run.

Frontend: manual `npx vercel --prod` from `frontend/` directory (auto-deploy not yet configured).

---

## Known Gotchas

- **CRITICAL — stream_update required:** Vertex AI indexes MUST use `--index-update-method=stream_update`. `batch_update` makes `upsert_datapoints()` silently fail.
- **Cloud Run 32 MB ingress limit:** Cloud Run rejects bodies over 32 MB before reaching the app. Frontend advertises 32 MB cap. True large-file support requires GCS signed URLs (v1.1 roadmap).
- **NEXT_PUBLIC_* vars baked at build time:** Setting them in Vercel dashboard requires a redeploy — they are not picked up at runtime.
- **Index provisioning time:** New indexes take 30–60 min to provision + 15–30 min to deploy to endpoint.
- **pydantic-settings env_file:** `config.py` only reads `.env` if the file exists at startup — prevents local dev config from leaking into the container if `.dockerignore` ever fails.
- **gcloud location:** `~/Downloads/google-cloud-sdk/bin/gcloud`

---

## GCP Reference

| Resource | Value |
|---|---|
| Project | `structureiq` |
| Project number | `381539677677` |
| Region | `us-east1` |
| Bucket | `gs://structureiq-docs` |
| Service account | `structureiq-sa@structureiq.iam.gserviceaccount.com` |
| Cloud Run service | `structureiq-backend` |
| Cloud Build trigger | `structureiq-main-deploy` (global, watches `main`) |

---

## Future State

See [ROADMAP.md](./ROADMAP.md) for the full product roadmap.

**v1.1:** Signed URL uploads (bypass 32 MB limit), Google OAuth, document history per user.
**v2.0:** Real-time collaboration, custom standards upload, webhook notifications, API access.
**v3.0:** Computer vision on job site photos, Procore/Autodesk integrations, continuous monitoring, mobile app.
