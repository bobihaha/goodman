#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash deploy/scripts/release_files.sh --release-name <name> --file-list <path> [options]

Options:
  --execute                 Execute release. Without this flag the script only dry-runs.
  --allow-root-collision    Allow same basename files at production project root. Use only after manual inspection.
  --release-name <name>     Release name used in backup directory. Letters, numbers, dot, dash and underscore only.
  --file-list <path>        Text file with one relative project file path per line. Blank lines and # comments are ignored.
  --services "<services>"   Docker Compose services to rebuild. Default: "app frontend".
  --remote <ssh-target>     SSH target. Default: deploy@47.100.81.73.
  --port <port>             SSH port. Default: 22222.
  --key <path>              SSH private key. Default: /Users/renhui/Desktop/aliyun.pem.
  --remote-dir <path>       Production project directory. Default: /home/deploy/iot_card_platform.

Examples:
  bash deploy/scripts/release_files.sh --release-name inventory_spec_board --file-list deploy/release_manifests/inventory_spec_board.txt
  bash deploy/scripts/release_files.sh --execute --release-name inventory_spec_board --file-list deploy/release_manifests/inventory_spec_board.txt
EOF
}

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
REMOTE="deploy@47.100.81.73"
REMOTE_PORT="22222"
REMOTE_KEY="/Users/renhui/Desktop/aliyun.pem"
REMOTE_DIR="/home/deploy/iot_card_platform"
SERVICES="app frontend"
RELEASE_NAME=""
FILE_LIST=""
EXECUTE=0
ALLOW_ROOT_COLLISION=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --execute)
      EXECUTE=1
      shift
      ;;
    --allow-root-collision)
      ALLOW_ROOT_COLLISION=1
      shift
      ;;
    --release-name)
      RELEASE_NAME="${2:-}"
      shift 2
      ;;
    --file-list)
      FILE_LIST="${2:-}"
      shift 2
      ;;
    --services)
      SERVICES="${2:-}"
      shift 2
      ;;
    --remote)
      REMOTE="${2:-}"
      shift 2
      ;;
    --port)
      REMOTE_PORT="${2:-}"
      shift 2
      ;;
    --key)
      REMOTE_KEY="${2:-}"
      shift 2
      ;;
    --remote-dir)
      REMOTE_DIR="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "${RELEASE_NAME}" || -z "${FILE_LIST}" ]]; then
  usage >&2
  exit 2
fi

if [[ ! "${RELEASE_NAME}" =~ ^[A-Za-z0-9._-]+$ ]]; then
  echo "Invalid release name: ${RELEASE_NAME}" >&2
  exit 2
fi

if [[ ! -f "${FILE_LIST}" ]]; then
  echo "File list does not exist: ${FILE_LIST}" >&2
  exit 2
fi

if [[ -z "${SERVICES}" || ! "${SERVICES}" =~ ^[A-Za-z0-9_.\ -]+$ ]]; then
  echo "Invalid services list: ${SERVICES}" >&2
  exit 2
fi

cd "${PROJECT_ROOT}"

RELEASE_FILES=()
while IFS= read -r file; do
  RELEASE_FILES+=("${file}")
done < <(
  sed 's/[[:space:]]*$//' "${FILE_LIST}" |
    sed '/^[[:space:]]*$/d;/^[[:space:]]*#/d'
)

if [[ "${#RELEASE_FILES[@]}" -eq 0 ]]; then
  echo "File list is empty after removing comments and blank lines: ${FILE_LIST}" >&2
  exit 2
fi

for file in "${RELEASE_FILES[@]}"; do
  if [[ "${file}" = /* || "${file}" == *".."* ]]; then
    echo "Only normal relative paths are allowed in file list: ${file}" >&2
    exit 2
  fi
  if [[ ! -f "${file}" ]]; then
    echo "Local release file does not exist: ${file}" >&2
    exit 2
  fi
done

REMOTE_TAR_FILES=()
for file in "${RELEASE_FILES[@]}"; do
  REMOTE_TAR_FILES+=("$(printf '%q' "${file}")")
done

SSH_OPTS=(-i "${REMOTE_KEY}" -p "${REMOTE_PORT}" -o BatchMode=yes -o ConnectTimeout=10)
SSH=(ssh "${SSH_OPTS[@]}" "${REMOTE}")
RSYNC_RSH="ssh -i ${REMOTE_KEY} -p ${REMOTE_PORT} -o BatchMode=yes"

echo "Release name: ${RELEASE_NAME}"
echo "Remote: ${REMOTE}:${REMOTE_DIR}"
echo "Services: ${SERVICES}"
echo "Mode: $([[ "${EXECUTE}" -eq 1 ]] && echo execute || echo dry-run)"
echo
printf 'Files:\n'
printf '  %s\n' "${RELEASE_FILES[@]}"
echo

echo "[1/7] Remote preflight"
"${SSH[@]}" "cd '${REMOTE_DIR}' && test -f docker-compose.yml && test -f check_system.sh && docker compose config >/dev/null && docker compose ps --format 'table {{.Name}}\t{{.Service}}\t{{.Status}}'"

echo "[2/7] Detect misplaced root files"
ROOT_COLLISIONS=()
for file in "${RELEASE_FILES[@]}"; do
  if [[ "${file}" == */* ]]; then
    base="$(basename "${file}")"
    if "${SSH[@]}" "cd '${REMOTE_DIR}' && test -f '${base}'"; then
      ROOT_COLLISIONS+=("${base}")
    fi
  fi
done

if [[ "${#ROOT_COLLISIONS[@]}" -gt 0 && "${ALLOW_ROOT_COLLISION}" -ne 1 ]]; then
  echo "Possible misplaced files exist at production project root:" >&2
  printf '  %s\n' "${ROOT_COLLISIONS[@]}" >&2
  echo "Remove or inspect them before release. Aborting." >&2
  exit 1
elif [[ "${#ROOT_COLLISIONS[@]}" -gt 0 ]]; then
  echo "Root basename collisions allowed after manual inspection:"
  printf '  %s\n' "${ROOT_COLLISIONS[@]}"
fi

echo "[3/7] Rsync dry-run with preserved paths"
rsync -anvzR -e "${RSYNC_RSH}" "${RELEASE_FILES[@]}" "${REMOTE}:${REMOTE_DIR}/"

if [[ "${EXECUTE}" -ne 1 ]]; then
  echo
  echo "Dry-run completed. Re-run with --execute to backup, sync, rebuild and verify."
  exit 0
fi

echo "[4/7] Production backup"
REMOTE_BACKUP_DIR="$(
  "${SSH[@]}" "cd '${REMOTE_DIR}' && set -euo pipefail
TS=\$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=\"release_backups/\${TS}_${RELEASE_NAME}\"
mkdir -p \"\${BACKUP_DIR}/mysql\" \"\${BACKUP_DIR}/redis\" \"\${BACKUP_DIR}/files\"
chmod 700 release_backups \"\${BACKUP_DIR}\" \"\${BACKUP_DIR}/mysql\" \"\${BACKUP_DIR}/redis\" \"\${BACKUP_DIR}/files\"
tar --ignore-failed-read -czf \"\${BACKUP_DIR}/files/source_files_\${TS}.tar.gz\" ${REMOTE_TAR_FILES[*]}
docker exec iot_mysql sh -lc 'exec mysqldump -uroot -p\"\$MYSQL_ROOT_PASSWORD\" --single-transaction --routines --triggers --events \"\$MYSQL_DATABASE\"' | gzip > \"\${BACKUP_DIR}/mysql/iot_card_platform_\${TS}.sql.gz\"
REDIS_PASSWORD_VALUE=\$(awk -F= '\$1==\"REDIS_PASSWORD\"{print substr(\$0,index(\$0,\"=\")+1)}' .env | tr -d '\r')
docker exec -e REDISCLI_AUTH=\"\${REDIS_PASSWORD_VALUE}\" iot_redis redis-cli --no-auth-warning BGSAVE >/dev/null
sleep 3
docker cp iot_redis:/data/dump.rdb \"\${BACKUP_DIR}/redis/dump_\${TS}.rdb\" >/dev/null
chmod 600 \"\${BACKUP_DIR}\"/mysql/* \"\${BACKUP_DIR}\"/redis/* \"\${BACKUP_DIR}\"/files/*
find \"\${BACKUP_DIR}\" -type f -printf \"%p %s bytes\\n\" | sort >&2
printf \"%s\" \"\${BACKUP_DIR}\""
)"
echo "Backup directory: ${REMOTE_BACKUP_DIR}"

echo "[5/7] Sync files"
rsync -avzR -e "${RSYNC_RSH}" "${RELEASE_FILES[@]}" "${REMOTE}:${REMOTE_DIR}/"

echo "[6/7] Build and restart services"
"${SSH[@]}" "cd '${REMOTE_DIR}' && docker compose up -d --build ${SERVICES}"

echo "[7/7] Health checks and log scan"
"${SSH[@]}" "cd '${REMOTE_DIR}' && set -euo pipefail
bash ./check_system.sh
sleep 30
docker compose ps --format 'table {{.Name}}\t{{.Service}}\t{{.Status}}'
echo '[internal backend health]'
docker compose exec -T app python - <<'PY'
import urllib.request
print(urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5).read().decode(), end='')
PY
echo
echo '[recent non-auth errors]'
docker logs iot_card_app --since 30s 2>&1 | grep -Ei 'error|exception|traceback|failed|失败' | grep -v '身份认证失败' | tail -n 80 || true"

echo
echo "Release completed."
echo "Backup directory: ${REMOTE_BACKUP_DIR}"
