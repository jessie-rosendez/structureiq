# StructureIQ Deployment Checklist

Run this checklist before every production deploy. Check each item before proceeding.

---

## Backend (Cloud Run via Cloud Build)

### Environment Variables (set in `cloudbuild.yaml` `--set-env-vars`)
- [x] `GOOGLE_CLOUD_PROJECT=structureiq`
- [x] `GCS_BUCKET_NAME=structureiq-docs`
- [x] `VERTEX_LOCATION=us-east1`
- [x] `GEMINI_LOCATION=global`
- [x] `GEMINI_MODEL=gemini-2.5-flash`
- [x] `LANGCHAIN_TRACING_V2=true`
- [x] `LANGCHAIN_PROJECT=structureiq`
- [x] `ENVIRONMENT=production`
- [x] `MAX_FILE_SIZE_MB=100`
- [x] `CHUNK_SIZE=1000`
- [x] `CHUNK_OVERLAP=200`
- [x] `RETRIEVAL_TOP_K_DOCS=5`
- [x] `RETRIEVAL_TOP_K_STANDARDS=3`
- [x] `CONFIDENCE_THRESHOLD=0.75`

### Secrets (injected via `--set-secrets`, stored in GCP Secret Manager)
- [x] `GOOGLE_API_KEY` → Secret Manager: `google-api-key:latest`
- [x] `LANGCHAIN_API_KEY` → Secret Manager: `langsmith-api-key:latest`

### Service Account (`structureiq-sa@structureiq.iam.gserviceaccount.com`)
- [x] `roles/aiplatform.user` — Vertex AI Vector Search + Gemini
- [x] `roles/storage.admin` — GCS bucket + Container Registry push
- [x] `roles/run.admin` — Cloud Run deploy
- [x] `roles/logging.logWriter` — Cloud Build logs
- [x] `roles/artifactregistry.writer` — Push images to Artifact Registry
- [x] `roles/secretmanager.secretAccessor` — Read secrets
- [x] `roles/iam.serviceAccountUser` — Act as service account

### Dockerfile
- [x] `credentials.json` excluded via `backend/.dockerignore`
- [x] `.env` excluded via `backend/.dockerignore`
- [x] Uses `libgl1` not `libgl1-mesa-glx` (renamed in Debian trixie)
- [x] Exposes port 8080

### CORS (`backend/app/main.py`)
- [x] `allow_origins` includes `localhost:3000`, `localhost:3001`
- [x] `allow_origin_regex` set to `https://.*\.vercel\.app` (wildcard subdomains)

---

## Frontend (Vercel)

### Environment Variables (set in Vercel project settings, NOT in `.env.local`)
- [x] `NEXT_PUBLIC_API_URL=https://structureiq-backend-eyyi6tggvq-ue.a.run.app`

> ⚠️ `.env.local` points to `localhost:8000` for local dev — Vercel must have its own env var set in the dashboard or via `vercel env add`, otherwise the deployed frontend calls localhost and fails with "Failed to fetch".

### Build
- [x] No unused imports (ESLint strict — will fail build if present)
- [x] No TypeScript errors

### Deploy command
```bash
npx vercel --prod
```

---

## Auto-Deploy (Cloud Build Trigger)
- [x] Trigger: `structureiq-main-deploy` (region: global)
- [x] Watches: `jessie-rosendez/structureiq` → `main` branch
- [x] Config: `cloudbuild.yaml` in repo root
- [x] Every `git push origin main` triggers a Cloud Run re-deploy automatically

---

## Verified Live URLs
- **Backend:** https://structureiq-backend-eyyi6tggvq-ue.a.run.app
- **Frontend:** https://frontend-7kn1e49h0-jessie-rosendezs-projects.vercel.app
- **Health check:** `curl https://structureiq-backend-eyyi6tggvq-ue.a.run.app/health`

---

## Common Failure Causes
| Symptom | Cause | Fix |
|---|---|---|
| "Failed to fetch" on Vercel | `NEXT_PUBLIC_API_URL` not set in Vercel env | `vercel env add NEXT_PUBLIC_API_URL production` then redeploy |
| Cloud Build: `cloudbuild.yaml not found` | File not committed to git | `git add cloudbuild.yaml && git push` |
| Cloud Build: permission denied push | SA missing `artifactregistry.writer` | Grant role via gcloud |
| Cloud Build: logging error | SA missing `logging.logWriter` | Grant role via gcloud |
| Query 404 model not found | Wrong Gemini model name or region | Check `GEMINI_MODEL` and `GEMINI_LOCATION` in cloudbuild.yaml |
| CORS blocked on new Vercel URL | `allow_origin_regex` not matching | Verify regex in `main.py` matches Vercel URL pattern |
