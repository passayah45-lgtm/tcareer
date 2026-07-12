# T-Career

T-Career is a Django REST Framework and Next.js career and learning platform. The backend is intentionally kept as a modular monolith: domains are separated into Django apps and service layers, but they deploy together until real scale pressure justifies extraction.

## Local Setup

1. Copy environment files:

```powershell
copy backend\.env.example backend\.env
copy frontend\.env.local.example frontend\.env.local
```

2. Start backend dependencies and API:

```powershell
docker compose up --build
```

3. Run migrations in a second terminal:

```powershell
docker compose exec api python manage.py migrate
```

4. Install and run the frontend:

```powershell
cd frontend
npm ci
npm run dev
```

Backend: `http://localhost:8000`

Frontend: `http://localhost:3000`

API docs: `http://localhost:8000/api/v1/schema/swagger-ui/`

## Environment Variables

Use `backend/.env.example` and `frontend/.env.local.example` as templates. Real `.env` files are ignored and must not be committed.

Important backend variables:

- `SECRET_KEY`
- `DATABASE_URL`
- `REDIS_URL`
- `CELERY_BROKER_URL`
- `FRONTEND_URL`
- `CORS_ALLOWED_ORIGINS`
- `CSRF_TRUSTED_ORIGINS`
- `STRIPE_WEBHOOK_SECRET`
- `MEDIACONVERT_WEBHOOK_SECRET`
- `AUTH_COOKIE_SECURE`
- `AUTH_COOKIE_SAMESITE`
- `SECURE_SSL_REDIRECT`

## Auth Flow

Login, registration, and Google auth return an access token in JSON and set the refresh token in an `HttpOnly` cookie. Refresh tokens are not returned in JSON response bodies.

Refresh and logout support the cookie flow. When the refresh cookie is used, clients must send `X-CSRFToken` matching the readable auth CSRF cookie.

## Organization Roles

Organization membership is scoped per organization. Supported scoped roles include:

- `student`
- `instructor`
- `mentor`
- `recruiter`
- `company_admin`
- `university_admin`
- `content_moderator`
- `finance_admin`
- `platform_admin`
- `super_admin`

Users cannot self-grant privileged roles. Privileged organization membership changes should go through service-layer methods.

## Permission System

Central object permission decisions live in `backend/common/permission_service.py`. New endpoints should call the permission service rather than adding scattered checks such as direct role string comparisons.

## Entitlement System

Central access and monetization decisions live in `backend/common/entitlements.py`. Payment providers should update subscriptions and future entitlement records through webhook handlers and services.

## Webhook Security

Webhook handlers must verify provider signatures or configured secrets before processing. In production, missing webhook secrets fail closed.

Current webhook paths:

- `POST /api/v1/payments/webhook/`
- `POST /api/v1/courses/webhooks/mediaconvert/`

## Audit And Analytics

Audit logs are append-only and stored in `apps.audit`. Analytics events are lightweight product events stored in `apps.analytics` so they can later be streamed to a warehouse.

## CI Pipeline

GitHub Actions runs:

- Backend tests
- Backend lint and format checks
- Python dependency audit
- Frontend `npm ci`
- Frontend type checking
- Frontend linting
- Frontend production build
- Frontend dependency audit

## Version 1.0 Release Candidate

Release-candidate notes, blocker register, operational checklist, risk register, and CTO verdict live in `docs/release-candidate-1.0.md`.
Production-readiness provider validation, retention, load-test, accessibility, monitoring, and go-live guidance live in `docs/production-readiness-1.0.md`.
Staging go-live rehearsal evidence is tracked in `docs/staging-go-live-rehearsal.md`.
VPS deployment setup and required GitHub secrets live in `docs/vps-deployment-runbook.md`.

Useful release commands:

```powershell
cd backend
python manage.py production_smoke_check
python manage.py backup_restore_check --dry-run
python manage.py release_candidate_check
python manage.py release_candidate_check --fail-on-warning
python manage.py validate_production_providers --json
python manage.py run_retention_policies --dry-run --json
```
