#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "${SCRIPT_DIR}/../../docker-compose.prod.yml" || -f "${SCRIPT_DIR}/../../docker-compose.yml" ]]; then
  PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
elif [[ -f "${SCRIPT_DIR}/docker-compose.prod.yml" || -f "${SCRIPT_DIR}/docker-compose.yml" ]]; then
  PROJECT_ROOT="${SCRIPT_DIR}"
else
  PROJECT_ROOT="$(pwd)"
fi
cd "${PROJECT_ROOT}"

REDIS_PASSWORD_VALUE=""
if [[ -f ".env" ]]; then
  REDIS_PASSWORD_VALUE="$(awk -F= '$1=="REDIS_PASSWORD"{sub(/^[^=]+=/,""); print; exit}' .env)"
fi

if [[ -f "docker-compose.prod.yml" ]]; then
  COMPOSE_FILE="docker-compose.prod.yml"
elif [[ -f "docker-compose.yml" ]]; then
  COMPOSE_FILE="docker-compose.yml"
else
  echo "No docker compose file found in ${PROJECT_ROOT}" >&2
  exit 1
fi

compose() {
  docker compose -f "${COMPOSE_FILE}" "$@"
}

SERVICES_CACHE="$(compose config --services 2>/dev/null || true)"

pick_service() {
  local primary="$1"
  local fallback="$2"

  if printf '%s\n' "${SERVICES_CACHE}" | grep -qx "${primary}"; then
    echo "${primary}"
    return
  fi

  if printf '%s\n' "${SERVICES_CACHE}" | grep -qx "${fallback}"; then
    echo "${fallback}"
    return
  fi

  echo ""
}

MYSQL_SERVICE="$(pick_service mysql mysql)"
REDIS_SERVICE="$(pick_service redis redis)"
BACKEND_SERVICE="$(pick_service backend app)"
FRONTEND_SERVICE="$(pick_service nginx frontend)"

if [[ -z "${MYSQL_SERVICE}" || -z "${REDIS_SERVICE}" || -z "${BACKEND_SERVICE}" || -z "${FRONTEND_SERVICE}" ]]; then
  echo "Failed to detect required services from ${COMPOSE_FILE}" >&2
  printf '%s\n' "${SERVICES_CACHE}"
  exit 1
fi

echo "Project root: ${PROJECT_ROOT}"
echo "Compose file: ${COMPOSE_FILE}"
echo "Services: mysql=${MYSQL_SERVICE}, redis=${REDIS_SERVICE}, backend=${BACKEND_SERVICE}, frontend=${FRONTEND_SERVICE}"
echo

echo "[1/7] Containers"
compose ps
echo

echo "[2/7] Container Stats"
container_ids="$(compose ps -q "${MYSQL_SERVICE}" "${REDIS_SERVICE}" "${BACKEND_SERVICE}" "${FRONTEND_SERVICE}" | tr '\n' ' ')"
if [[ -n "${container_ids// }" ]]; then
  docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" ${container_ids}
else
  echo "No running containers found"
fi
echo

echo "[3/7] Backend Health"
compose exec -T "${BACKEND_SERVICE}" python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5).read().decode())"
echo

echo "[4/7] Frontend Health"
curl -fsS -o /tmp/check_system_frontend.out -w "time_total=%{time_total} code=%{http_code}\n" http://127.0.0.1/
head -c 200 /tmp/check_system_frontend.out || true
echo
echo

echo "[5/7] MySQL Status"
compose exec -T "${MYSQL_SERVICE}" sh -lc 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -Nse "
SHOW GLOBAL STATUS WHERE Variable_name IN (
  \"Threads_connected\",
  \"Threads_running\",
  \"Max_used_connections\",
  \"Slow_queries\"
);
SHOW GLOBAL VARIABLES WHERE Variable_name IN (
  \"max_connections\",
  \"innodb_buffer_pool_size\"
);"'
echo

echo "[6/7] Redis Status"
REDIS_CONTAINER_ID="$(compose ps -q "${REDIS_SERVICE}")"
if [[ -n "${REDIS_PASSWORD_VALUE}" ]]; then
  docker exec "${REDIS_CONTAINER_ID}" redis-cli -a "${REDIS_PASSWORD_VALUE}" INFO memory | grep -E "^maxmemory:"
else
  docker exec "${REDIS_CONTAINER_ID}" redis-cli INFO memory | grep -E "^maxmemory:"
fi
echo

echo "[7/7] Recent Backend Logs"
compose logs --tail 50 "${BACKEND_SERVICE}"
