# StructureIQ Frontend

Next.js 14 (App Router) · TypeScript · Tailwind CSS

## Live

**https://frontend-phi-five-58.vercel.app**

## Local Dev

```bash
npm install
npm run dev        # http://localhost:3000
```

Requires `frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_MAX_UPLOAD_MB=100
```

## Deploy

```bash
npx vercel --prod
```

`NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_MAX_UPLOAD_MB` must be set in the Vercel dashboard — they are baked into the build at deploy time, not read at runtime.

## Pages

| Route | Description |
|---|---|
| `/` | Upload page — drag-and-drop PDF/PNG/JPG, redirects to `/query` on success |
| `/query` | Chat interface — compliance Q&A with source inspector panel |
| `/report` | Full compliance report — 10 queries across ADA, OSHA, IBC, ASHRAE |

## Backend

Cloud Run: `https://structureiq-backend-eyyi6tggvq-ue.a.run.app`

See root [DEPLOY_CHECKLIST.md](../DEPLOY_CHECKLIST.md) and [PROGRESS.md](../PROGRESS.md) for full infrastructure details.
