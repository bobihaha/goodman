#!/usr/bin/env bash

set -euo pipefail

compose_file="${COMPOSE_FILE:-}"
env_file="${ENV_FILE:-}"
min_free_gb="${MIN_DEPLOY_FREE_GB:-10}"

if [[ -n "$compose_file" && -z "$env_file" ]] || [[ -z "$compose_file" && -n "$env_file" ]]; then
  echo "ERROR: COMPOSE_FILE and ENV_FILE must be set together" >&2
  exit 1
fi

if [[ -z "$compose_file" ]]; then
  if [[ -f docker-compose.yml && -f .env ]]; then
    compose_file="docker-compose.yml"
    env_file=".env"
  elif [[ -f docker-compose.prod.yml && -f .env.production ]]; then
    compose_file="docker-compose.prod.yml"
    env_file=".env.production"
  else
    echo "ERROR: no matching compose/environment file pair found" >&2
    exit 1
  fi
fi

echo "[1/5] Checking required files"
test -f "$env_file"
test -f "$compose_file"
echo "Compose file: $compose_file"
echo "Environment file: $env_file"

echo "[2/5] Checking Docker"
docker --version >/dev/null
docker compose version >/dev/null
docker info >/dev/null

echo "[3/5] Checking compose config"
docker compose --env-file "$env_file" -f "$compose_file" config >/dev/null

echo "[4/5] Checking free disk space"
df -h .
if [[ ! "$min_free_gb" =~ ^[0-9]+$ ]] || (( min_free_gb < 1 )); then
  echo "ERROR: MIN_DEPLOY_FREE_GB must be a positive integer" >&2
  exit 1
fi
available_kb="$(df -Pk . | awk 'NR == 2 {print $4}')"
required_kb="$((min_free_gb * 1024 * 1024))"
if (( available_kb < required_kb )); then
  echo "ERROR: less than ${min_free_gb}GB free; stop deployment and clean disk safely first" >&2
  exit 1
fi

echo "[5/5] Planned containers"
docker compose --env-file "$env_file" -f "$compose_file" ps

echo "Predeploy check passed"
