#!/usr/bin/env sh
set -eu

BASE_URL="${1:-}"
if [ -z "$BASE_URL" ]; then
  echo "Usage: $0 https://staging.tcareer.example [load-profile]" >&2
  exit 2
fi

LOAD_PROFILE="${2:-smoke}"
API_URL="${API_URL:-$BASE_URL/api/v1}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.staging.yml}"
ENV_FILE="${ENV_FILE:-.env.staging}"

if [ ! -f "$ENV_FILE" ]; then
  echo "$ENV_FILE is missing. Copy env.example.staging to $ENV_FILE on the staging host and fill secrets outside source control." >&2
  exit 2
fi

run_step() {
  name="$1"
  shift
  echo "==> $name"
  "$@"
}

run_step "Docker Compose config validation" docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" config
run_step "Build staging images" docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" build
run_step "Start staging stack" docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d
run_step "Release candidate check" docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T web python manage.py release_candidate_check --json
run_step "Production smoke check" docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T web python manage.py production_smoke_check
run_step "Provider configuration check" docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T web python manage.py validate_production_providers --json
run_step "Retention dry run" docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T web python manage.py run_retention_policies --dry-run --json
run_step "Backup restore readiness probe" docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T web python manage.py backup_restore_check --dry-run --fail-on-warning

if [ "${SKIP_LOAD_TEST:-0}" != "1" ]; then
  run_step "Load test profile: $LOAD_PROFILE" python tools/load_tests/tcareer_load.py --base-url "$API_URL" --profile "$LOAD_PROFILE"
fi

echo "Staging rehearsal command sequence completed. Review output before marking any step passed."
