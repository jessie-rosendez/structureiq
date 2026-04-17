# StructureIQ Roadmap

> StructureIQ is designed as a foundation, not a feature. Every architectural decision made in v1.0 was made with this roadmap in mind.

---

## Known Infrastructure Gotchas (Hard-Won)

- **Vertex AI index update method:** Always create indexes with `--index-update-method=stream_update`. The default (`batch_update`) silently breaks `upsert_datapoints()` — documents ingest without error but are never queryable. This burned a full provisioning cycle (60+ min) in v1.0 development.
- **Index provisioning is not instant:** Even empty indexes take 30–60 min to provision, plus another 15–30 min to deploy to an endpoint. Build this wait into any infrastructure automation or CI pipeline.
- **Cloud Run 32 MB ingress hard limit:** Cloud Run rejects payloads over 32 MB at the load balancer layer before the app ever sees them. App-level middleware cannot override this. True large-file upload requires GCS signed URLs (on the v1.1 roadmap).

---

## Immediate Post-MVP (v1.1)

- **Signed URL upload pattern for files over 32 MB** — bypass Cloud Run's ingress limit by generating a GCS signed URL client-side and uploading directly to the bucket; only the metadata and trigger hit the backend
- **User authentication via Google OAuth** — gate the platform per user, associate documents and reports to accounts, enable audit trails
- **Document history** — persist past uploads and compliance reports per user; retrieve and re-query previous sessions without re-uploading

---

## Short Term (v2.0)

- **Real-time collaboration** — multiple engineers reviewing the same document simultaneously; shared chat thread, synchronized compliance findings, comment threading per finding
- **Custom standards upload** — firms bring their own internal standards, specs, or client requirements to ground against; same two-layer RAG pipeline, extended to n layers
- **Webhook notifications** — alert via email or Slack when a compliance report is ready for large documents or batch runs
- **API access** — let third-party tools query StructureIQ programmatically; OpenAPI-documented endpoints with API key auth for Procore plugins, BIM integrations, and internal tooling

---

## Long Term Vision (v3.0)

- **Computer vision on construction photos** — identify OSHA violations from job site images automatically; flag missing PPE, unsecured scaffolding, protruding rebar, unsafe ladders using Gemini Vision at scale
- **Integration with Procore, Autodesk Construction Cloud, Bluebeam** — pull documents directly from project management platforms; push compliance findings back as RFIs or issue logs
- **Continuous monitoring** — re-run compliance checks automatically when standards are updated (e.g., new IBC edition published); notify owners of previously-passing documents that now require review
- **Multi-language support** — Spanish, French for international AEC firms and cross-border projects
- **Mobile app for field inspectors** — capture job site photos, run instant OSHA checks, generate field reports without returning to the office
