#!/usr/bin/env bash

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups/redis}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

mkdir -p "${BACKUP_DIR}"

docker exec iot_redis redis-cli BGSAVE >/dev/null
sleep 3
docker cp iot_redis:/data/dump.rdb "${BACKUP_DIR}/dump_${TIMESTAMP}.rdb"

echo "Redis backup created: ${BACKUP_DIR}/dump_${TIMESTAMP}.rdb"
