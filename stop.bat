@echo off
setlocal enabledelayedexpansion
title Stop PayPilot Services
color 0C

cd /d "%~dp0"

echo ===============================================================================
echo                      STOPPING PAYPILOT SERVICES
echo ===============================================================================
echo.

echo [1/2] Terminating backend & frontend processes on ports 8000 and 5173...
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000,5173 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }" >nul 2>&1

echo [2/2] Terminating lingering PayPilot console windows...
taskkill /f /t /fi "WINDOWTITLE eq PayPilot Backend*" >nul 2>&1
taskkill /f /t /fi "WINDOWTITLE eq PayPilot Frontend*" >nul 2>&1

echo.
echo [OK] All PayPilot services and processes on ports 8000 and 5173 stopped.
echo ===============================================================================
ping 127.0.0.1 -n 2 >nul 2>&1
