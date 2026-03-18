#!/usr/bin/env bash

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups/mysql}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
FILE_PATH="${BACKUP_DIR}/iot_card_platform_${TIMESTAMP}.sql.gz"

mkdir -p "${BACKUP_DIR}"

docker exec iot_mysql sh -lc 'exec mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" --single-transaction --routines --triggers --events "$MYSQL_DATABASE"' \
  | gzip > "${FILE_PATH}"

echo "Backup created: ${FILE_PATH}"
