#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir"
mode="${1:-start}"
docker compose -p agv-pkg6 -f docker-compose.online.yml config --quiet
case "$mode" in
  build) docker compose -p agv-pkg6 -f docker-compose.online.yml build agv-vision-pkg6-online ;;
  start) ;;
  *) echo "Usage: bash start_docker_online.sh [build|start]" >&2; exit 2 ;;
esac
docker compose -p agv-pkg6 -f docker-compose.online.yml up -d --no-build --pull never agv-vision-pkg6-online
echo "Container started; check logs and health before using the camera."
