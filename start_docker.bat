@echo off
setlocal

cd /d "%~dp0"

echo [AGV] Starting agv-vision by docker compose...
docker compose up -d --build
if errorlevel 1 (
  echo [AGV] Start failed. Please check Docker Desktop and compose plugin.
  pause
  exit /b 1
)

echo [AGV] agv-vision is running on http://127.0.0.1:8010
exit /b 0
