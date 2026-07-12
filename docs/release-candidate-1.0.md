# T-Career Version 1.0 Release Candidate

This document records the Version 1.0 release-candidate audit for the current modular-monolith platform. It is intentionally critical: passing tests is required, but it does not by itself make the platform production-ready.

## Release Status

Status: Controlled pilot ready after validation, not public production ready.

Rationale:

- Core product domains are implemented: learning, certificates, careers, resumes, portfolios, jobs, recruiter workflows, organizations, enterprise reporting, notifications, email delivery, trust, AI products, and RAG.
- The platform has centralized permission, entitlement, candidate visibility, audit, analytics, email, health, and AI service layers.
- Production operations now include health endpoints, smoke checks, backup checks, provider webhook verification, Redis enforcement, worker status, RAG freshness, and a release-candidate check.
- Remaining risks are mainly operational hardening, provider validation, scale testing, accessibility completion, and enterprise tenant-isolation depth testing.

## Release Commands

Run from `backend/` with the same environment used by the target deployment:

```powershell
python manage.py check --deploy
python manage.py makemigrations --check --dry-run
python manage.py production_smoke_check
python manage.py backup_restore_check --dry-run
python manage.py release_candidate_check
python manage.py release_candidate_check --fail-on-warning
python manage.py reindex_ai_knowledge --dry-run --limit 50
python manage.py process_email_deliveries --dry-run --limit 50
python manage.py process_data_exports --limit 50
```

Frontend release checks:

```powershell
npm run type-check
npm run lint
npm run build
npm audit --audit-level=high --omit=dev
```

Backend release checks:

```powershell
pytest -q
```

## Architecture Audit

Strengths:

- The modular monolith remains the right architecture. Domains are isolated enough for team ownership while avoiding premature distributed-system complexity.
- Security and operations logic is increasingly centralized in `common` services, Django settings, management commands, and domain services.
- AI products now route through the centralized AI platform and RAG services rather than direct provider calls.
- Tenant isolation exists in the major recruiter, enterprise, candidate visibility, export, and knowledge retrieval surfaces.

High-priority findings:

- Several large domain services and views remain oversized, especially jobs, organizations, and AI platform services.
- API response shapes are mostly standardized through `StandardRenderer`, but a few legacy/manual responses remain intentional compatibility exceptions.
- Provider-backed services are interface-ready, but some need real production provider validation before public launch.
- Performance budgets exist for important endpoints, but load testing with realistic data volumes is still missing.

## API Contract Audit

Standard:

- Success responses are wrapped by `common.renderers.StandardRenderer`.
- Errors are normalized by `common.exceptions.custom_exception_handler` with `detail`, `code`, and field-level validation data where applicable.
- Pagination uses `common.pagination.StandardPagination` by default; some manually paginated legacy job endpoints preserve their existing shape for frontend compatibility.
- Sensitive file downloads remain explicit responses and must enforce object-level authorization before returning any URL or file.

Intentional legacy exceptions:

- Some public job and search endpoints use lightweight custom pagination metadata.
- Some health endpoints use plain JSON renderers so infrastructure probes can consume predictable raw JSON.
- Existing frontend clients expect certain domain-specific nested payloads in recruiter, organization, and AI routes.

## Permission And Tenant Isolation Audit

Controls in place:

- `PermissionService` owns organization, job, portfolio, resume, certificate, verification, payment, and entitlement checks.
- `CandidateVisibilityService` is the authority for recruiter profile, resume, portfolio, contact, and unlock decisions.
- `EntitlementService` gates recruiter monetization and AI/product access decisions.
- RAG retrieval filters public, organization, private owner, enrolled learner, instructor, unlocked recruiter, and platform-admin access paths.

Release requirement:

- Any new sensitive endpoint must include a negative cross-tenant test before merge.
- Admin override behavior must be explicit and audited.

## Security Checklist

Required before pilot:

- `DEBUG=False` in production-like environments.
- Non-empty `SECRET_KEY`, `ALLOWED_HOSTS`, `DATABASE_URL`, `REDIS_URL`, and secure frontend origins.
- Redis-backed cache and throttling in production.
- `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`, `AUTH_COOKIE_SECURE=True`.
- Provider-specific email webhooks in production; shared-secret fallback disabled.
- Upload validation enabled for private resumes, portfolio media, branding assets, and verification documents.
- Refresh tokens stored in HttpOnly cookies and not returned in JSON.
- AI privacy redaction, moderation, feature flags, budgets, and audit logging enabled.

## Performance Review

Measured with query-budget tests:

- Student dashboard
- Recruiter dashboard
- Candidate search
- Application detail
- Job detail
- Notification history

Known performance risks:

- Candidate search needs production-grade search infrastructure when profile volume grows.
- RAG retrieval currently uses deterministic local/provider-ready adapters; real vector backend benchmarking is still required.
- Analytics, audit, email delivery, AI usage, and retrieval event tables need retention/partitioning plans before large-scale usage.

Future caching opportunities:

- Public course/job browse lists.
- Organization analytics summaries.
- Recruiter dashboard aggregates.
- AI admin quality and RAG freshness cards.

## Background Worker Reliability

Covered worker areas:

- Email delivery processing.
- Job alert processing.
- Data export processing.
- Knowledge reindexing.
- AI evaluation jobs.

Readiness expectations:

- Commands must be idempotent or safely retryable.
- Failed and pending work must be visible through `/api/v1/health/ops/` and `release_candidate_check`.
- Long-running jobs should store progress, status, retry count, failure reason, and audit events.

## Accessibility Audit

Priority screens checked by code review:

- Login and registration.
- Public jobs and job detail.
- Student dashboard, resumes, portfolio, and applications.
- Recruiter dashboard, jobs, pipeline, candidate search, and application detail.
- Organization dashboard, import/export, analytics, settings, and audit.
- AI chat, learning tutor, interview coach, and AI admin.

Known gaps:

- Keyboard-only drag-and-drop alternatives should be tested manually in the recruiter pipeline.
- Some dense analytics cards need screen-reader polish and better table alternatives.
- Full WCAG 2.2 AA verification requires manual assistive technology testing, not just lint/build checks.

## Release Blocker Register

P0 blockers:

- None identified in this pass after the release checks are run successfully.

P1 before public production:

- Run a realistic load test for candidate search, dashboards, RAG retrieval, notifications, and AI history.
- Validate provider integrations in staging: SMTP, SES/SendGrid/Mailgun webhooks, S3/private storage, Redis, Celery, Sentry, and Stripe.
- Complete manual WCAG 2.2 AA review of the highest-traffic screens.
- Add retention/archival jobs for audit logs, analytics events, AI usage, retrieval events, and email delivery history.
- Expand cross-tenant regression coverage for every enterprise report/import/export route with seeded multi-organization data.

P2 accepted pilot limitations:

- Vector backends are provider-ready but not benchmarked with production vector infrastructure.
- Some API endpoints keep legacy response shapes for frontend compatibility.
- Email templates are safe and functional, but not yet fully branded.
- Several admin and organization screens are operationally useful but not yet polished for non-technical operators.

P3 future enhancements:

- Dedicated search backend for candidate and job discovery.
- Data warehouse export for analytics events.
- Fine-grained AI evaluation dashboards by customer organization.
- Automated accessibility snapshots and keyboard journey tests.

## Risk Register

| Risk | Severity | Likelihood | Evidence | Mitigation | Release impact |
| --- | --- | --- | --- | --- | --- |
| Provider integrations not fully proven | High | Medium | Many provider paths are abstraction-ready but need staging credentials | Run staging smoke tests for SMTP, webhook providers, S3, Redis, Celery, Sentry, and Stripe | P1 |
| Search scalability | High | Medium | Candidate/job search relies on relational filtering and lightweight scoring | Add OpenSearch/Postgres full-text plan and load tests | P1 |
| Data growth in audit/analytics/AI tables | Medium | High | Append-heavy tables are central to trust and analytics | Add retention, export, partitioning, and dashboard monitoring | P1 |
| Accessibility gaps | Medium | Medium | Static review exists, manual assistive testing remains | Run WCAG 2.2 AA manual review and fix keyboard/focus/table issues | P1 |
| Oversized services | Medium | Medium | Jobs, organizations, and AI platform services contain broad responsibilities | Refactor gradually behind service boundaries with regression tests | P2 |
| RAG quality variability | Medium | Medium | Retrieval eval exists but needs larger golden datasets | Expand retrieval datasets and CI gates by product | P2 |
| AI answer quality and fairness | High | Medium | AI outputs are evaluated but still probabilistic | Human review, disclaimers, eval gates, prompt security tests, and feedback loops | P1 |
| Enterprise tenant isolation depth | High | Low-Medium | Major paths are covered; exhaustive multi-tenant tests still needed | Add route-by-route cross-tenant test matrix | P1 |
| Background worker stuck jobs | Medium | Medium | Status/retry exists, but automated stuck-job recovery is limited | Add stuck-job detector and runbook alerts | P2 |
| Backup restore confidence | High | Low-Medium | Backup check is readiness-oriented, not a full restore rehearsal | Run scheduled restore rehearsal against staging | P1 |

## Platform Health Score

- Architecture: 8/10. The modular monolith is coherent and still appropriate.
- Security: 7/10. Strong controls exist, but provider staging validation and manual review remain.
- Tenant Isolation: 7/10. Central services cover major paths; exhaustive route matrix is still needed.
- Privacy: 7/10. Candidate visibility, private downloads, and RAG filters are in place.
- Performance: 6/10. Query budgets exist, but realistic load testing is missing.
- Scalability: 6/10. Current design can pilot; search, analytics, and retention need scale work.
- Maintainability: 7/10. Service boundaries are improving, though some services are large.
- Code Quality: 7/10. Tests are broad and patterns are consistent.
- Frontend Quality: 7/10. Main flows exist with state handling; polish and a11y need more time.
- Accessibility: 6/10. Basic improvements exist, but manual WCAG verification is incomplete.
- Backend Quality: 8/10. DRF services, tests, and ops checks are strong for a pilot.
- Testing: 7/10. Unit/integration coverage is meaningful; full E2E and load coverage are next.
- DevOps: 7/10. Health, smoke, backup, queue, and release checks exist.
- Monitoring: 6/10. Structured logs and health endpoints exist; alerting dashboards are pending.
- Backup and Recovery: 6/10. Checks and docs exist; restore rehearsal is still needed.
- AI Readiness: 7/10. Central AI platform patterns are sound.
- AI Safety: 7/10. Moderation, privacy, budgets, audit, and evaluation exist; real-world evaluation must expand.
- RAG Readiness: 6/10. Foundation is solid; production vector backend validation is pending.
- Enterprise Readiness: 6/10. Core enterprise workflows exist; compliance and operational polish remain.
- Production Readiness: 5/10. Too many P1 items remain for public production.
- Pilot Readiness: 7/10. Controlled pilot is reasonable with close monitoring.
- Investor Readiness: 7/10. Product breadth and architecture are compelling, with clear risk register.

## CTO Verdict

1. Release T-Career Version 1.0 publicly today: No.
2. Approve a controlled pilot: Yes, if validation passes and participants are limited.
3. Unresolved P0 blockers: None identified after successful release checks.
4. Five highest risks: provider validation, tenant-isolation completeness, search/load performance, AI/RAG quality, and data-retention/backup maturity.
5. P1 before public production: load tests, staging provider tests, manual accessibility review, retention/archival jobs, and full cross-tenant route matrix.
6. Tenant isolation maturity: good enough for controlled pilot, not yet enterprise public production.
7. AI beta safety: acceptable for beta with feature flags, budgets, and disclaimers.
8. RAG beta reliability: acceptable for limited beta, not yet broad production.
9. Architecture: keep the modular monolith.
10. Next step: run RC validation, fix any command/test failures, then complete P1 production-readiness work before public launch.
