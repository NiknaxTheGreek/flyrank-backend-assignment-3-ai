#!/usr/bin/env bash
set -Eeuo pipefail

# Run this on a Docker-capable machine. It proves the Compose stack, HTTP CRUD,
# direct PostgreSQL state, and named-volume persistence without using Replit.
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_NAME="flyrank_assignment3_verify_${RANDOM}_${RANDOM}"
API_PORT="${API_PORT:-18000}"
POSTGRES_USER="verify_user"
POSTGRES_PASSWORD="verify_password"
POSTGRES_DB="verify_db"
ENV_FILE="$(mktemp)"
COMPOSE=(docker compose --project-name "$PROJECT_NAME" --env-file "$ENV_FILE" -f "$PROJECT_DIR/docker-compose.yml")

cleanup() {
  "${COMPOSE[@]}" down -v --remove-orphans >/dev/null 2>&1 || true
  rm -f "$ENV_FILE"
}
trap cleanup EXIT

cat >"$ENV_FILE" <<EOF
POSTGRES_USER=$POSTGRES_USER
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_DB=$POSTGRES_DB
API_PORT=$API_PORT
EOF

json_field() {
  python3 -c "import json, sys; print(json.load(sys.stdin)['$1'])"
}

wait_for_api() {
  for _ in $(seq 1 45); do
    if curl --fail --silent "http://127.0.0.1:${API_PORT}/health" >/dev/null; then
      return 0
    fi
    sleep 1
  done
  "${COMPOSE[@]}" logs
  echo "API health endpoint did not become ready." >&2
  return 1
}

echo "Starting isolated Compose project: $PROJECT_NAME"
"${COMPOSE[@]}" up --build --detach
wait_for_api

seed_count="$(curl --fail --silent "http://127.0.0.1:${API_PORT}/tasks" | python3 -c 'import json, sys; print(len(json.load(sys.stdin)))')"
test "$seed_count" = "3"

created="$(curl --fail --silent --request POST "http://127.0.0.1:${API_PORT}/tasks" \
  --header "Content-Type: application/json" \
  --data '{"title":"Docker persistence check","description":"Created by the external verifier.","completed":false}')"
task_id="$(printf '%s' "$created" | json_field id)"

curl --fail --silent "http://127.0.0.1:${API_PORT}/tasks/${task_id}" >/dev/null
curl --fail --silent --request PUT "http://127.0.0.1:${API_PORT}/tasks/${task_id}" \
  --header "Content-Type: application/json" \
  --data '{"completed":true}' \
  | python3 -c 'import json, sys; assert json.load(sys.stdin)["completed"] is True'

stored_title="$("${COMPOSE[@]}" exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc \
  "SELECT title FROM tasks WHERE id = ${task_id}")"
test "$stored_title" = "Docker persistence check"

echo "Restarting without -v to prove named-volume persistence."
"${COMPOSE[@]}" down
"${COMPOSE[@]}" up --detach
wait_for_api

persisted="$(curl --fail --silent "http://127.0.0.1:${API_PORT}/tasks/${task_id}")"
printf '%s' "$persisted" | python3 -c 'import json, sys; payload=json.load(sys.stdin); assert payload["title"] == "Docker persistence check"; assert payload["completed"] is True'

echo "Docker runtime verification passed."