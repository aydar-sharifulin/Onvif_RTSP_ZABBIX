#!/usr/bin/env bash
set -euo pipefail

# Ограничитель для запуска camcheck.py из Zabbix.
# Не допускает повторную одновременную проверку одного IP
# и завершает зависшую проверку по таймауту.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

IP="${1:-}"
TIMEOUT_SEC="${CAMCHECK_TIMEOUT:-25}"

if [[ -z "$IP" ]]; then
    echo '{"status":"error","error":"IP address is required"}'
    exit 0
fi

# IP/hostname преобразуем в безопасное имя файла.
LOCK_ID="$(printf '%s' "$IP" | tr -c 'A-Za-z0-9_.-' '_')"
LOCKFILE="/tmp/camcheck_${LOCK_ID}.lock"

exec 9>"$LOCKFILE"

# Если этот IP уже проверяется — не запускаем второй процесс.
if ! flock -n 9; then
    echo '{"status":"busy","info":"camcheck already running for this IP"}'
    exit 0
fi

export OPENCV_FFMPEG_LOGLEVEL=-8
export OPENCV_LOG_LEVEL=OFF

PYTHON_BIN="${CAMCHECK_PYTHON:-${SCRIPT_DIR}/venv/bin/python}"

if [[ ! -x "$PYTHON_BIN" ]]; then
    PYTHON_BIN="/usr/bin/python3"
fi

OUT=""
RC=0

OUT=$(
    timeout -k 2 "$TIMEOUT_SEC" \
        "$PYTHON_BIN" -W ignore \
        "${SCRIPT_DIR}/camcheck.py" "$@" 2>/dev/null
) || RC=$?

if [[ $RC -eq 124 || $RC -eq 137 ]]; then
    echo "{\"status\":\"error\",\"error\":\"Timeout after ${TIMEOUT_SEC}s\"}"
    exit 0
fi

if [[ -z "$OUT" ]]; then
    echo '{"status":"error","error":"Empty output from camcheck.py"}'
    exit 0
fi

echo "$OUT"
