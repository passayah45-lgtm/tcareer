# T-Career VPS Deployment Runbook

This runbook deploys T-Career to a single VPS with Docker Compose. It replaces
the old AWS ECS deployment workflow and is suitable for staging, demos, and an
early controlled pilot.

## GitHub Secrets

Configure these repository secrets in GitHub:

- `VPS_HOST`: VPS IP address or hostname.
- `VPS_PORT`: SSH port. Use `22` if unchanged.
- `VPS_USER`: Linux user used for deployment.
- `VPS_SSH_KEY`: private SSH key allowed to connect to the VPS.
- `VPS_DEPLOY_PATH`: dedicated deployment folder, for example `/opt/tcareer`.

The deployment workflow is manual only:

1. Open GitHub Actions.
2. Select `Deploy to VPS`.
3. Click `Run workflow`.
4. Deploy `main` or a specific commit SHA.

## VPS Prerequisites

Install Docker and the Docker Compose plugin on the VPS.

Create a dedicated deploy directory:

```bash
sudo mkdir -p /opt/tcareer
sudo chown -R "$USER:$USER" /opt/tcareer
```

Create the production environment file on the VPS only:

```bash
cd /opt/tcareer
cp env.example.production .env.production
nano .env.production
```

Do not commit `.env.production` to Git. Fill every secret with real values.

## Required Environment Values

At minimum, configure:

- `SECRET_KEY`
- `ALLOWED_HOSTS`
- `FRONTEND_URL`
- `NEXT_PUBLIC_API_URL`
- `POSTGRES_PASSWORD`
- `DATABASE_URL`
- `REDIS_PASSWORD`
- `REDIS_URL`
- `DJANGO_CACHE_LOCATION`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `CORS_ALLOWED_ORIGINS`
- `CSRF_TRUSTED_ORIGINS`
- SMTP settings if email should send

For a same-domain deployment, a common shape is:

```env
ALLOWED_HOSTS=tcareerjobs.com,www.tcareerjobs.com,localhost,127.0.0.1
FRONTEND_URL=https://tcareerjobs.com
NEXT_PUBLIC_API_URL=https://tcareerjobs.com/api/v1
CORS_ALLOWED_ORIGINS=https://tcareerjobs.com,https://www.tcareerjobs.com
CSRF_TRUSTED_ORIGINS=https://tcareerjobs.com,https://www.tcareerjobs.com
APP_PORT=8001
FRONTEND_PORT=3001
```

These ports intentionally differ from the T-Food deployment so both projects can
share the same VPS IP address.

Production Django trusts Nginx HTTPS termination through `X-Forwarded-Proto`.
Keep `proxy_set_header X-Forwarded-Proto $scheme;` in the API, admin, and media
Nginx locations so `SECURE_SSL_REDIRECT=True` does not create an HTTPS redirect
loop behind the reverse proxy.

## What The Workflow Does

The GitHub Action:

1. Checks out the selected ref.
2. Connects to the VPS over SSH.
3. Syncs source files to `VPS_DEPLOY_PATH`.
4. Preserves `.env.production`, media, static files, database volumes, and Redis volumes.
5. Builds Docker images on the VPS.
6. Starts Postgres and Redis.
7. Runs Django migrations.
8. Runs `collectstatic`.
9. Starts web, frontend, Celery worker, and Celery beat.
10. Runs `production_smoke_check`.

## Reverse Proxy

Put Nginx, Caddy, or another TLS reverse proxy in front of the containers.

Suggested routing:

- `https://tcareerjobs.com/` to frontend on `127.0.0.1:3001`
- `https://tcareerjobs.com/api/` to backend on `127.0.0.1:8001`
- `https://tcareerjobs.com/admin/` to backend on `127.0.0.1:8001`

Keep ports `3001` and `8001` firewalled from the public internet if possible.

## Manual Commands On VPS

```bash
cd /opt/tcareer
docker compose --env-file .env.production -f docker-compose.prod.yml build
docker compose --env-file .env.production -f docker-compose.prod.yml up -d db redis
docker compose --env-file .env.production -f docker-compose.prod.yml run --rm web python manage.py migrate --noinput
docker compose --env-file .env.production -f docker-compose.prod.yml run --rm web python manage.py collectstatic --noinput
docker compose --env-file .env.production -f docker-compose.prod.yml up -d
docker compose --env-file .env.production -f docker-compose.prod.yml exec -T web python manage.py production_smoke_check
```

To validate the Compose file locally with the example environment:

```bash
TCAREER_ENV_FILE=env.example.production docker compose --env-file env.example.production -f docker-compose.prod.yml config
```

## Rollback

Run the GitHub workflow again with a previous commit SHA.

If operating manually on the VPS, redeploy the previous source snapshot and run:

```bash
cd /opt/tcareer
docker compose --env-file .env.production -f docker-compose.prod.yml build
docker compose --env-file .env.production -f docker-compose.prod.yml up -d
```

## Notes

- This workflow does not create DNS records, TLS certificates, or secrets.
- Public production still requires provider validation, backups, monitoring, TLS,
  and restore rehearsal evidence.
