# T-Career Version 1.0 Production Readiness

This pass closes operational foundations needed before public production. It does not approve a public launch by itself because real provider validation, measured load tests, manual accessibility review, and a restore rehearsal require a staging environment with production-like credentials and data.

## Provider Validation

Command:

```powershell
python manage.py validate_production_providers --json
python manage.py validate_production_providers --fail-on-warning
python manage.py validate_production_providers --email --storage --redis --celery --sentry --stripe --ai --vector
```

Provider status in this workspace:

| Provider | Status | Evidence | Release decision |
| --- | --- | --- | --- |
| PostgreSQL | Configuration validated | `DATABASE_URL` and migrations are checked by smoke/RC commands | Live staging test required |
| Redis | Configuration validated locally | Cache probe and production Redis enforcement exist | Live staging test required |
| Celery | Configuration validated | Broker URL and registered task count checked | Live worker visibility required |
| SMTP | Configuration-only locally | Local environment uses console/locmem style backends | Live staging send required |
| Email webhooks | Automated tests | SES, SendGrid, Mailgun verification tests exist | Provider callback staging test required |
| S3 private storage | Configuration-only locally | Bucket settings checked, local storage used here | Live signed URL test required |
| S3 public media/branding | Configuration-only locally | Public bucket setting checked | Live object access test required |
| Sentry | Configuration-only locally | DSN/env/release metadata checked | Staging event required |
| Stripe | Configuration validated | Secret/webhook presence checked | Live test-mode webhook required |
| AI providers | Configuration validated | Real-provider flag and provider credentials checked | Staging model call required |
| Vector backend | Configuration validated | Backend health abstraction checked | pgvector/OpenSearch benchmark required |

## Load Test Foundation

Script:

```powershell
python tools/load_tests/tcareer_load.py --base-url http://localhost:8000 --profile smoke
python tools/load_tests/tcareer_load.py --base-url https://staging-api.example.com --profile pilot --token <access-token> --organization-id <org-id>
```

Profiles:

| Profile | Concurrent users | Duration | Purpose |
| --- | ---: | ---: | --- |
| smoke | 2 | 30s | Endpoint availability |
| pilot | 15 | 3m | Controlled pilot confidence |
| expected-production | 75 | 5m | Launch target |
| stress | 150 | 10m | Saturation discovery |

Scenarios:

- Authentication and health.
- Student dashboard.
- Recruiter dashboard.
- Organization dashboard.
- Job browsing.
- Candidate search.
- Application pipeline.
- Notification history.
- AI history.
- AI chat.
- RAG retrieval.
- Enterprise reports.
- Email queue status.

Success criteria:

- Error rate below 1% for smoke and pilot.
- p95 below the endpoint budget for smoke and pilot.
- No database, Redis, Celery, email, or RAG freshness degradation during the run.
- No cross-tenant records visible in responses.

Failure criteria:

- Any 5xx spike above 1%.
- Authentication/session errors not caused by test token expiry.
- p95 above budget for two consecutive runs.
- Worker backlog grows without recovery.

## Performance Budgets

Initial release budgets:

| Endpoint area | p50 | p95 | p99 | Error rate | Query count | Response size |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Student dashboard | 300ms | 900ms | 1500ms | <1% | <=65 | <=250KB |
| Recruiter dashboard | 300ms | 900ms | 1500ms | <1% | <=35 | <=250KB |
| Organization dashboard | 400ms | 1200ms | 2000ms | <1% | TBD | <=350KB |
| Candidate search | 500ms | 1500ms | 2500ms | <1% | <=25 in regression fixture | <=500KB |
| Job listing | 250ms | 800ms | 1400ms | <1% | TBD | <=350KB |
| Application pipeline | 500ms | 1500ms | 2500ms | <1% | TBD | <=500KB |
| RAG retrieval | 600ms | 1500ms | 3000ms | <1% | bounded by retrieval timeout | <=300KB |
| AI history | 400ms | 1200ms | 2000ms | <1% | TBD | <=350KB |
| Notification history | 250ms | 700ms | 1200ms | <1% | <=6 | <=250KB |

Dedicated search service trigger:

- Candidate or job search p95 exceeds 1500ms with production-sized data.
- Query plans show repeated sequential scans on large profile/job tables.
- Relevance requirements exceed simple SQL filtering and scoring.
- Faceting/counts become a material part of recruiter workflows.

## Tenant-Isolation Matrix

Sensitive route groups requiring cross-tenant tests:

| Area | Read isolation | Write isolation | List/count isolation | Current status |
| --- | --- | --- | --- | --- |
| Organizations | Required | Required | Required | Covered by service/view tests, expand route matrix |
| Enterprise departments/teams/cohorts | Required | Required | Required | Covered in enterprise tests |
| Imports/exports/reports | Required | Required | Required | Covered by enterprise tests, add larger fixtures |
| Recruiter jobs/applications | Required | Required | Required | Covered by recruiter/revenue tests |
| Candidate search/unlocks | Required | Required | Required | Covered by hardening tests |
| Resumes/portfolios/private downloads | Required | Required | Required | Covered by candidate visibility tests |
| Notifications | Owner-only | Owner-only | Owner-only | Covered by notification tests |
| Audit logs | Organization/platform scoped | Append-only | Scoped | Covered by platform ops tests |
| AI recruiter tools | Organization scoped | Organization scoped | Scoped | Needs broader route matrix |
| RAG knowledge | Source permission scoped | Admin-only indexing | Scoped | Covered by RAG tests |
| Private storage | Authorized download only | Owner/admin only | No file metadata leak | Covered by storage tests, staging S3 needed |

Rule: every new sensitive route must include a negative organization-A versus organization-B regression test before release.

## Retention and Archival

Command:

```powershell
python manage.py run_retention_policies --dry-run --json
python manage.py run_retention_policies --data-type email_deliveries --dry-run
python manage.py run_retention_policies --data-type export_files --organization-id <org-id> --archive --delete --limit 100
```

Safety:

- Dry-run/report-only unless `--delete` is explicitly passed.
- Audit logs are append-only and are not deleted by this command.
- Export jobs with legal hold are skipped.
- Executed retention batches create an audit event.
- Organization-scoped retention is supported where models carry organization IDs.

Configured data types:

- Audit logs.
- Analytics events.
- Notifications.
- Email deliveries.
- AI requests.
- AI usage.
- AI feedback.
- AI evaluations/results.
- RAG retrieval logs.
- Export files.
- Import files.
- Failed worker jobs.

## Backup and Restore Rehearsal

Current status: not live-rehearsed in this workspace.

Required staging rehearsal:

1. Take database backup.
2. Take media/private-storage inventory.
3. Restore database to isolated staging database.
4. Restore or remount media and private storage.
5. Run migrations.
6. Verify login, organization membership, applications, certificates, audit logs, AI records, and RAG metadata.
7. Run `production_smoke_check`, `backup_restore_check --storage-probe`, and `release_candidate_check`.
8. Record RPO, RTO, restored record counts, failed checks, and rollback decision.

Target RPO: 24 hours for pilot, 4 hours before public production.

Target RTO: 4 hours for pilot, 1 hour before public production.

## Accessibility Report

Fixed in this pass:

- Added a keyboard-visible skip link.
- Added a stable `main-content` target wrapping app content.

Manual checks still required:

- Login and registration.
- Student dashboard, course player, quiz, resumes, portfolio, applications.
- Jobs and job detail.
- Recruiter pipeline and application detail.
- Organization console.
- Notification/privacy settings.
- AI chat, Interview Coach, Learning Tutor.

Known risk:

- Drag/drop and dense dashboard components need keyboard-only and screen-reader review before public beta.

## Monitoring and Alerting

Production alert matrix:

| Alert | Severity | Escalation |
| --- | --- | --- |
| API 5xx error rate > 1% for 5 minutes | P1 | On-call engineer |
| p95 latency over budget for 10 minutes | P2/P1 by endpoint | Backend owner |
| Database connectivity failure | P0 | Immediate page |
| Redis/cache failure | P0/P1 | Immediate page |
| Celery worker outage | P1 | Platform owner |
| Email backlog growing for 15 minutes | P2 | Notifications owner |
| Export/import failed jobs spike | P2 | Enterprise owner |
| AI failed jobs or cost spike | P1/P2 | AI owner |
| Moderation/safety spike | P1 | AI safety owner |
| RAG indexing failure/freshness degradation | P2 | AI platform owner |
| Storage errors/private download failures | P1 | Platform owner |
| Webhook failures/rejections spike | P1 | Payments/email owner |
| Repeated login failures/rate limits | P1/P2 | Security owner |

Release metadata:

- `APP_VERSION`
- `API_VERSION`
- `GIT_SHA`
- `BUILD_DATE`
- `SENTRY_RELEASE`
- `DEPLOY_ENVIRONMENT`

## AI and RAG Release Gates

Public rollout requires:

- Feature flag enabled only for intended cohorts.
- Budget policy configured for organization/user/feature.
- Provider health check passes.
- Moderation enabled.
- Privacy redaction enabled.
- Evaluation pass rate above product threshold.
- No unresolved high/critical safety events.
- RAG freshness without failed/stale critical documents.
- Vector backend health passes.
- Citations contain only retrieved sources and safe metadata.
- Retrieval confidence monitored by product area.

Current status: acceptable for controlled pilot, not broad public rollout.

## Staging Rehearsal Evidence

The staging rehearsal evidence register lives in `docs/staging-go-live-rehearsal.md`.

Do not mark Version 1.0 public-production ready until that document has live provider validation, measured load-test results, manual accessibility findings, monitoring alert results, and verified restore RPO/RTO.

## Go-Live Checklist

1. Run full backend and frontend validation.
2. Run `validate_production_providers --fail-on-warning` in staging.
3. Run pilot load profile and record p50/p95/p99/error rate.
4. Complete manual WCAG checks.
5. Complete restore rehearsal.
6. Review tenant-isolation matrix.
7. Confirm alerts are routed.
8. Freeze release metadata.
9. Publish release notes.
10. Run smoke checks immediately after deploy.

## Rollback Checklist

1. Stop deploy rollout.
2. Preserve logs and failed job state.
3. Disable risky feature flags.
4. Roll back application version.
5. Run health ready/live checks.
6. Re-run provider validation.
7. Verify login, dashboards, applications, notifications, and AI disabled/limited state.
8. Document incident timeline and customer impact.
