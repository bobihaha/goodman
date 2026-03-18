#!/usr/bin/env bash

set -euo pipefail

if [ "${1:-}" = "" ]; then
  echo "Usage: $0 <backup.sql.gz>"
  exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "${BACKUP_FILE}" ]; then
  echo "Backup file not found: ${BACKUP_FILE}"
  exit 1
fi

gunzip -c "${BACKUP_FILE}" | docker exec -i iot_mysql sh -lc 'exec mysql -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE"'

echo "Restore completed from: ${BACKUP_FILE}"
