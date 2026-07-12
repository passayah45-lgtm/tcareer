# T-Career Version 1.0 Staging Go-Live Rehearsal

This document is the required evidence register for the Version 1.0 staging go-live rehearsal.

Current evidence status: blocked for public-production approval.

Reason: this workspace does not include a live staging deployment, production-like provider credentials, staging domain, staging object storage, Stripe test webhook forwarding, Sentry project, production vector backend, or restored staging database. Configuration and local validation are useful, but they are not live provider validation.

Prepared staging artifacts:

- `docker-compose.staging.yml` for a production-like small-pilot stack.
- `env.example.staging` for non-secret staging environment placeholders.
- `deploy/nginx/staging.conf` for HTTPS reverse proxy routing.
- `frontend/Dockerfile` for standalone Next.js staging/prod containers.
- `tools/staging/run_staging_rehearsal.ps1` and `tools/staging/run_staging_rehearsal.sh` for ordered operator execution.
- `docs/staging-infrastructure-runbook.md` for deployment, DNS, HTTPS, provider, load, restore, accessibility, and pilot guardrails.
- `docs/staging-evidence-template.md` for measurable evidence capture.
- `docs/tenant-isolation-route-matrix.md` for route-level tenant-isolation closure.

## Infrastructure Used

Local validation used:

- SQLite local database.
- Local filesystem storage.
- Local/cache test settings.
- Mock/local AI provider configuration.
- Local Next.js production build.
- Local management commands and backend tests.
- Prepared staging Compose topology with PostgreSQL, Redis, Django API, Next.js frontend, Celery worker, Celery Beat, and Nginx reverse proxy.

Not available in this workspace:

- Staging PostgreSQL.
- Staging Redis.
- Staging Celery worker and Beat processes.
- SMTP/provider credentials.
- S3 private/public buckets.
- Sentry DSN.
- Stripe test webhook endpoint.
- Real AI provider key for restricted staging prompt.
- pgvector/OpenSearch production vector backend.
- HTTPS staging domain.

## Provider Validation Results

| Provider | Status | Evidence | Blocker |
| --- | --- | --- | --- |
| PostgreSQL | Not tested live | Local migration checks passed only | Need staging DB connection and restore drill |
| Redis | Partially validated | Local cache/provider check passed | Need staging Redis cache/throttle/broker test |
| Celery | Partially validated | Broker config/task registration checked | Need live worker, Beat, retry, failed-task test |
| SMTP/email provider | Not tested live | Local config warning only | Need authenticated staging send and webhook callbacks |
| Email webhooks | Partially validated | Automated SES/SendGrid/Mailgun tests exist | Need provider callback against staging URL |
| Private storage | Not tested live | Local storage only | Need private upload/signed download/denial test |
| Public media/branding storage | Not tested live | Local storage only | Need public object upload/delete in staging prefix |
| Stripe test mode | Not tested live | Config checks only | Need subscription, duplicate webhook, invalid signature, cancellation |
| Sentry | Not tested live | DSN absent locally | Need handled/unhandled staging events with release metadata |
| AI provider | Not tested live | Mock provider local checks only | Need restricted real-provider prompt, moderation, budget, failure handling |
| Vector backend | Partially validated | Local vector backend healthy | Need pgvector/OpenSearch indexing/retrieval/update/stale/latency test |

Runbook: use `docs/staging-infrastructure-runbook.md` and capture final results in `docs/staging-evidence-template.md`.

## Load-Test Evidence

Tool:

```powershell
python tools/load_tests/tcareer_load.py --base-url https://staging.tcareer.example/api/v1 --profile smoke
python tools/load_tests/tcareer_load.py --base-url https://staging.tcareer.example/api/v1 --profile pilot --token <access-token> --organization-id <org-id>
```

No live staging load test was executed from this workspace.

Required result table for staging:

| Scenario | Profile | Users | Duration | Requests | Success | Failed | Error rate | RPS | p50 | p95 | p99 | Result |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| authentication | smoke | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Blocked |
| student dashboard | pilot | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Blocked |
| recruiter dashboard | pilot | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Blocked |
| organization dashboard | pilot | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Blocked |
| job browsing | pilot | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Blocked |
| candidate search | pilot | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Blocked |
| RAG retrieval | pilot | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Blocked |

## Backup and Restore Rehearsal

Status: not verified.

Required evidence:

1. Database backup command and backup identifier.
2. Storage snapshot or object inventory.
3. Post-backup test records.
4. Restore target environment.
5. Migration output after restore.
6. Authentication verification.
7. Organization tenant-boundary verification.
8. Course/enrollment verification.
9. Application/interview verification.
10. Certificate verification.
11. Audit log verification.
12. AI record verification.
13. RAG metadata verification.
14. Private storage authorization verification.
15. RPO and RTO.

Current RPO: not measured.

Current RTO: not measured.

## Accessibility Review

Automated/local evidence:

- Frontend lint passed.
- Frontend build passed.
- Global skip link and main landmark target exist.

Manual WCAG 2.2 AA review: not completed in this workspace.

Required manual matrix:

| Screen | Keyboard | Focus | Labels | Errors | Headings | Contrast | SR status | Zoom | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Login | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Blocked |
| Registration | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Blocked |
| Student dashboard | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Blocked |
| Course player | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Blocked |
| Recruiter pipeline | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Blocked |
| Organization console | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Blocked |
| AI chat | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Blocked |

## Tenant-Isolation Route Matrix

Coverage status:

- Existing automated tests cover organization services/views, enterprise workflows, candidate visibility, recruiter jobs/applications, RAG privacy, private resume access, notification ownership, and platform operations.
- A route-level matrix has been started in `docs/tenant-isolation-route-matrix.md`. Rows marked `Partial` or `Needs review` must be closed before public beta.

Minimum matrix columns:

- Endpoint.
- Method.
- Auth required.
- Roles.
- Organization scope.
- Ownership rule.
- Platform admin override.
- Audit event.
- Positive test.
- Cross-tenant negative test.
- ID-guessing negative test.
- List/count leakage test.

## Ruff Adoption

Chosen strategy: Option B.

- Establish a reviewed legacy backlog.
- Enforce Ruff on new and modified files.
- Keep full Ruff visible in CI/reporting until the backlog is burned down.
- Do not disable security/correctness rules merely for green output.

Latest local evidence:

- Full `ruff check .`: failed with 2,792 existing findings.
- Full `ruff format --check .`: failed with 165 files requiring formatting.
- Files changed in the production-readiness pass pass Ruff check and format.

## Schema Warning Review

Status: not closed.

Observed class of warnings:

- drf-spectacular duplicate operation IDs.
- drf-spectacular serializer inference warnings for function-based/APIView endpoints.
- Local deployment security warnings caused by DEBUG/local environment.

Release decision:

- Warnings affecting generated clients for authentication, payments, organizations, jobs, resumes, private downloads, and AI/RAG endpoints must be fixed or explicitly accepted before public beta.

## Monitoring Verification

Status: not live verified.

Required alert evidence:

- API 5xx spike.
- High latency.
- Database failure.
- Redis failure.
- Celery worker loss.
- Email backlog.
- Failed exports/imports.
- Failed AI jobs.
- AI cost threshold.
- Moderation spike.
- RAG indexing/freshness failure.
- Storage failure.
- Webhook failure.
- Repeated failed logins.

## AI and RAG Gates

Local evidence:

- AI platform tests pass.
- RAG privacy and retrieval tests pass.
- Local vector backend is healthy.

Blocked staging evidence:

- Real AI provider restricted prompt.
- Real moderation provider path.
- Real budget/cost telemetry.
- Production vector backend latency.
- Retrieval confidence on realistic staging corpus.
- Citation safety on production-like content.

## Go-Live Rehearsal Results

| Step | Result | Evidence |
| --- | --- | --- |
| Deploy release | Blocked | No staging deployment available |
| Run migrations | Passed locally | Migration drift clean |
| release_candidate_check | Passed with local warnings | Missing GIT_SHA/BUILD_DATE |
| production_smoke_check | Passed with local warnings | Email provider not configured |
| validate_production_providers | Passed with local warnings | Live providers absent |
| Verify workers | Blocked | No live staging workers |
| Seed pilot data | Blocked | No staging DB |
| Student journey | Blocked | No staging browser/API target |
| Instructor journey | Blocked | No staging browser/API target |
| Recruiter journey | Blocked | No staging browser/API target |
| Organization-admin journey | Blocked | No staging browser/API target |
| Platform-admin journey | Blocked | No staging browser/API target |
| AI/RAG gates | Partially validated locally | Real provider/vector blocked |
| Pilot load profile | Blocked | No staging target |
| Monitoring alerts | Blocked | No monitoring stack |
| Rollback rehearsal | Blocked | No staging deploy/rollback pipeline |

## Release Decision

Version 1.0 public production: not ready.

Controlled pilot: conditionally acceptable only after a real staging rehearsal fills the blocked evidence above.
