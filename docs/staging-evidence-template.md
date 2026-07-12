# T-Career Staging Evidence Template

Use this template during the live staging rehearsal. Do not paste secrets, raw tokens, provider signing keys, or private user data.

## Release

- App version:
- Git SHA:
- Build date:
- Environment:
- Staging URL:
- API URL:
- Operator:
- Rehearsal date:

## Infrastructure Provisioned

| Component | Status | Endpoint/Identifier | Evidence | Notes |
| --- | --- | --- | --- | --- |
| Django API | Blocked | TBD | TBD |  |
| Next.js frontend | Blocked | TBD | TBD |  |
| PostgreSQL | Blocked | TBD | TBD |  |
| Redis | Blocked | TBD | TBD |  |
| Celery worker | Blocked | TBD | TBD |  |
| Celery Beat | Blocked | TBD | TBD |  |
| Reverse proxy / HTTPS | Blocked | TBD | TBD |  |
| Private object storage | Blocked | TBD | TBD |  |
| Public object storage | Blocked | TBD | TBD |  |
| Email provider | Blocked | TBD | TBD |  |
| Sentry/monitoring | Blocked | TBD | TBD |  |
| Stripe test mode | Blocked | TBD | TBD |  |
| Restricted AI provider | Blocked | TBD | TBD |  |
| Vector backend | Blocked | TBD | TBD |  |

## Provider Validation

| Provider | Result | Live validated? | Evidence | Failure/Blocker |
| --- | --- | --- | --- | --- |
| PostgreSQL | TBD | TBD | TBD | TBD |
| Redis | TBD | TBD | TBD | TBD |
| Celery | TBD | TBD | TBD | TBD |
| Email | TBD | TBD | TBD | TBD |
| Email webhooks | TBD | TBD | TBD | TBD |
| Storage private | TBD | TBD | TBD | TBD |
| Storage public | TBD | TBD | TBD | TBD |
| Stripe test mode | TBD | TBD | TBD | TBD |
| Sentry | TBD | TBD | TBD | TBD |
| AI provider | TBD | TBD | TBD | TBD |
| Vector backend | TBD | TBD | TBD | TBD |

## Validation Commands

Paste sanitized command status only.

| Command | Status | Evidence |
| --- | --- | --- |
| backend targeted tests | TBD | TBD |
| full backend tests | TBD | TBD |
| tenant-isolation tests | TBD | TBD |
| migration drift | TBD | TBD |
| Django deployment checks | TBD | TBD |
| OpenAPI generation | TBD | TBD |
| Ruff check | TBD | TBD |
| Ruff format check | TBD | TBD |
| frontend type-check | TBD | TBD |
| frontend lint | TBD | TBD |
| frontend build | TBD | TBD |
| frontend audit | TBD | TBD |
| release_candidate_check | TBD | TBD |
| production_smoke_check | TBD | TBD |
| validate_production_providers | TBD | TBD |
| run_retention_policies dry run | TBD | TBD |
| backup_restore_check | TBD | TBD |
| staging seed | TBD | TBD |
| load-test smoke | TBD | TBD |
| load-test pilot | TBD | TBD |
| load-test expected-production | TBD | TBD |

## Load-Test Results

| Profile | Users | Duration | Requests | Successes | Failures | Error rate | RPS | p50 | p95 | p99 | DB load | Redis status | Queue depth | Result |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| smoke | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| pilot | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| expected-production | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

## Accessibility Results

| Screen | Critical | Serious | Moderate | Minor | Fixed | Remaining | Result |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Login | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Student dashboard | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Course player | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Job application | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Recruiter pipeline | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Organization console | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Platform admin | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| AI chat | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

## Backup and Restore

- Backup start:
- Backup finish:
- Restore start:
- Restore finish:
- Actual RTO:
- Actual RPO:
- Missing records:
- Failed checks:
- Manual steps:
- Automation gaps:

## Go-Live Rehearsal Result

| Step | Result | Evidence |
| --- | --- | --- |
| Deployment | TBD | TBD |
| Migrations | TBD | TBD |
| Provider validation | TBD | TBD |
| Worker verification | TBD | TBD |
| Pilot seed | TBD | TBD |
| Student journey | TBD | TBD |
| Instructor journey | TBD | TBD |
| Recruiter journey | TBD | TBD |
| Organization admin journey | TBD | TBD |
| Platform admin journey | TBD | TBD |
| AI gates | TBD | TBD |
| RAG gates | TBD | TBD |
| Load test | TBD | TBD |
| Monitoring alert tests | TBD | TBD |
| Backup restore | TBD | TBD |
| Rollback | TBD | TBD |

## Decision

Choose one based on measured evidence:

- Not ready
- Internal testing ready
- Controlled pilot ready
- Public beta ready
- Production ready

Decision:

Remaining P0 blockers:

Remaining P1 blockers:
