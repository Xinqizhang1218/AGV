#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "[AGV] Starting online service with docker-compose.online.yml ..."
docker compose -f docker-compose.online.yml up -d --build

echo "[AGV] agv-vision-online is running on http://127.0.0.1:8088"
