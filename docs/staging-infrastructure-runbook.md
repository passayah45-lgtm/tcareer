# T-Career Staging Infrastructure Runbook

This runbook prepares a production-like staging environment for the Version 1.0 go-live rehearsal. It does not certify production readiness by itself. Every result must be backed by live staging evidence.

## Topology

- Reverse proxy: Nginx terminates HTTPS and routes `/api/`, `/admin/`, `/static/`, and `/media/` to Django; all other paths route to Next.js.
- Frontend: standalone Next.js container.
- Backend: Django REST API served by Gunicorn.
- Workers: Celery worker and Celery Beat.
- Data services: PostgreSQL 16 and Redis 7.
- Providers: SMTP/email provider, Sentry, Stripe test mode, public/private object storage, restricted AI provider, and production vector backend.

## Files

- `docker-compose.staging.yml`: production-like staging stack.
- `env.example.staging`: placeholder environment variables. Copy to `.env.staging` on the staging host only.
- `deploy/nginx/staging.conf`: reverse proxy template for `staging.tcareer.example`.
- `tools/staging/run_staging_rehearsal.ps1`: Windows/PowerShell operator script.
- `tools/staging/run_staging_rehearsal.sh`: POSIX operator script.
- `docs/staging-go-live-rehearsal.md`: evidence register.

## Domain and HTTPS

Replace placeholders before deployment:

- Public app: `https://staging.tcareer.example`
- API base: `https://staging.tcareer.example/api/v1`
- Allowed hosts: `staging.tcareer.example,api.staging.tcareer.example`
- CORS allowed origins: `https://staging.tcareer.example`
- CSRF trusted origins: `https://staging.tcareer.example`
- Webhook callback URL pattern: `https://staging.tcareer.example/api/v1/<provider>/webhooks/`

DNS:

1. Create an `A` or `CNAME` record for `staging.tcareer.example`.
2. Issue a staging TLS certificate using the organization-approved CA.
3. Mount certificate paths using `TLS_CERT_PATH` and `TLS_KEY_PATH`.
4. Confirm the reverse proxy redirects HTTP to HTTPS.

## Deployment

On the staging host:

```bash
cp env.example.staging .env.staging
# Fill .env.staging using secret manager values. Do not commit it.
docker compose --env-file .env.staging -f docker-compose.staging.yml config
docker compose --env-file .env.staging -f docker-compose.staging.yml build
docker compose --env-file .env.staging -f docker-compose.staging.yml up -d
```

The `migrate` service runs before the web, worker, and Beat services start. If migrations fail, the dependent services should not start.

## Provider Validation

Run:

```bash
docker compose --env-file .env.staging -f docker-compose.staging.yml exec -T web python manage.py release_candidate_check --json
docker compose --env-file .env.staging -f docker-compose.staging.yml exec -T web python manage.py production_smoke_check --fail-on-warning
docker compose --env-file .env.staging -f docker-compose.staging.yml exec -T web python manage.py validate_production_providers --json --fail-on-warning
```

Record provider status as `live validated`, `partially validated`, `failed`, or `not tested`.

## Load Testing

Run against the staging API URL:

```bash
python tools/load_tests/tcareer_load.py --base-url https://staging.tcareer.example/api/v1 --profile smoke
python tools/load_tests/tcareer_load.py --base-url https://staging.tcareer.example/api/v1 --profile pilot --token <token> --organization-id <org-id>
python tools/load_tests/tcareer_load.py --base-url https://staging.tcareer.example/api/v1 --profile expected-production --token <token> --organization-id <org-id>
```

Release targets:

- Standard endpoint p95 below 1.5 seconds.
- Complex search and analytics p95 below 3 seconds.
- Normal API error rate below 1 percent.
- No sustained worker backlog after completion.

## Backup and Restore Rehearsal

Run a real restore into an isolated restore environment. The local command is only a readiness probe:

```bash
docker compose --env-file .env.staging -f docker-compose.staging.yml exec -T web python manage.py backup_restore_check --storage-probe --fail-on-warning
```

Do not mark backup restore complete until the restored app passes authentication, tenant isolation, courses, jobs, certificates, audit records, AI records, RAG metadata, and private storage authorization checks.

## Accessibility Rehearsal

Review these screens manually against WCAG 2.2 AA:

- Login and registration.
- Student dashboard, course player, quiz, jobs, applications, resumes, portfolio.
- Recruiter dashboard, pipeline, application detail, candidate search.
- Organization dashboard, reports, import/export, branding.
- Platform dashboard, operations, verification, audit.
- AI chat, interview coach, learning tutor, career coach.

Critical and serious issues must be fixed before pilot approval.

## Pilot Guardrails

Recommended controlled pilot limits:

- Organizations: 3
- Students: 150
- Recruiters: 15
- Instructors: 10
- AI budget: 25 USD/day
- Email: controlled test domains plus approved pilot users only
- Uploads: 10 MB private documents, 25 MB general media
- Job postings: 50 active jobs total
- Candidate search: throttled and audited
- Duration: 14 days

Rollback triggers:

- Any confirmed cross-tenant data leak.
- API error rate above 5 percent for 15 minutes.
- Authentication, email, or private storage outage lasting more than 15 minutes.
- AI provider cost exceeds daily budget.
- Worker backlog does not recover within 30 minutes.
