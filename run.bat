@echo off
setlocal enabledelayedexpansion

:: Set console title and color
title PayPilot - AI Revenue Operating System
color 0B

:: Ensure working directory is the project root
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo ===============================================================================
echo            PAYPILOT -- AI REVENUE OPERATING SYSTEM (BUILDATHON)
echo ===============================================================================
echo.
echo [1/5] Checking prerequisites...

:: 1. Detect Python interpreter
set "PYTHON_CMD="
if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    set "PYTHON_CMD=%SCRIPT_DIR%.venv\Scripts\python.exe"
    echo [INFO] Found local virtual environment Python.
)
if "%PYTHON_CMD%"=="" (
    where python >nul 2>&1
    if !errorlevel! equ 0 set "PYTHON_CMD=python"
)
if "%PYTHON_CMD%"=="" (
    where py >nul 2>&1
    if !errorlevel! equ 0 set "PYTHON_CMD=py"
)

if "%PYTHON_CMD%"=="" (
    color 0C
    echo [ERROR] Python is not found in PATH or .venv!
    echo Please install Python 3.11+ from https://www.python.org/downloads/
    echo Make sure to check Add Python to PATH during installation.
    echo.
    pause
    exit /b 1
)

%PYTHON_CMD% --version
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Failed to execute Python command: %PYTHON_CMD%
    pause
    exit /b 1
)

:: 2. Detect Frontend Package Manager (bun preferred, npm fallback)
set "BUN_CMD="
if exist "%USERPROFILE%\.bun\bin\bun.exe" (
    set "BUN_CMD=%USERPROFILE%\.bun\bin\bun.exe"
    echo [INFO] Found Bun package manager at %USERPROFILE%\.bun\bin\bun.exe
) else (
    where bun >nul 2>&1
    if !errorlevel! equ 0 set "BUN_CMD=bun"
)

if "%BUN_CMD%"=="" (
    where node >nul 2>&1
    if !errorlevel! neq 0 (
        color 0C
        echo [ERROR] Neither Bun nor Node.js found in PATH!
        pause
        exit /b 1
    )
    where npm >nul 2>&1
    if !errorlevel! neq 0 (
        color 0C
        echo [ERROR] npm is not found in PATH!
        pause
        exit /b 1
    )
    set "FRONTEND_RUN=npm run dev"
    echo [OK] Using Node.js / npm.
) else (
    set "FRONTEND_RUN=%BUN_CMD% run dev"
    echo [OK] Using Bun.
)

echo [OK] Python and Frontend runtime detected.
echo.

:: 3. Configure Root & Frontend Environment Files
echo [2/5] Checking environment configuration...
if not exist ".env" (
    if exist ".env.example" (
        echo Copying .env.example to .env ...
        copy /y ".env.example" ".env" >nul
        echo [OK] Created root .env file.
    )
) else (
    echo [OK] Root .env file exists.
)

if not exist "frontend\.env" (
    if exist "frontend\.env.example" (
        echo Copying frontend\.env.example to frontend\.env ...
        copy /y "frontend\.env.example" "frontend\.env" >nul
        echo [OK] Created frontend\.env file.
    )
) else (
    echo [OK] Frontend .env file exists.
)
echo.

:: 4. Check Python Dependencies
echo [3/5] Verifying backend dependencies...
%PYTHON_CMD% -c "import fastapi, uvicorn, sqlalchemy, pydantic" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing backend Python requirements...
    %PYTHON_CMD% -m pip install -r requirements.txt
    if !errorlevel! neq 0 (
        color 0C
        echo [ERROR] Failed to install Python dependencies.
        pause
        exit /b 1
    )
) else (
    echo [OK] Python dependencies verified.
)
echo.

:: 5. Check Frontend Dependencies
echo [4/5] Verifying frontend dependencies...
if not exist "frontend\node_modules\" (
    echo Installing frontend packages...
    pushd "%SCRIPT_DIR%frontend"
    if not "%BUN_CMD%"=="" (
        call "%BUN_CMD%" install
    ) else (
        call npm install
    )
    popd
) else (
    echo [OK] Frontend node_modules verified.
)
echo.

:: 6. Ensure Database is Initialized and Seeded
echo [5/5] Initializing / verifying database dataset...
%PYTHON_CMD% -m backend.app.data.seed >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Database verified / seeded successfully.
) else (
    echo [NOTE] Database initialization step completed.
)
echo.

:: 7. Clean existing listeners on ports 8000 and 5173 to avoid duplicates
echo Terminating any previous PayPilot listeners on ports 8000 and 5173...
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000,5173 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }" >nul 2>&1

:: 8. Launch Backend and Frontend in separate windows
echo ===============================================================================
echo                 LAUNCHING PAYPILOT FULL-STACK SERVICES
echo ===============================================================================
echo.
echo Starting FastAPI Backend on http://localhost:8000 ...
start "PayPilot Backend (FastAPI - Port 8000)" /D "%SCRIPT_DIR%." cmd /k "title PayPilot Backend (FastAPI - Port 8000) && color 0A && echo Starting FastAPI Backend on http://localhost:8000 ... && %PYTHON_CMD% -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload"

echo Starting Frontend Dev Server on http://localhost:5173 ...
start "PayPilot Frontend (Vite - Port 5173)" /D "%SCRIPT_DIR%frontend" cmd /k "title PayPilot Frontend (Vite - Port 5173) && color 0E && echo Starting Frontend UI on http://localhost:5173 ... && %FRONTEND_RUN%"

echo.
echo [INFO] Waiting for servers to initialize...
ping 127.0.0.1 -n 4 >nul 2>&1

:: Open browser
echo [INFO] Opening PayPilot Web Application in your browser...
start http://localhost:5173
start http://localhost:8000/docs

echo.
echo ===============================================================================
echo                           PAYPILOT CONTROL HUB
echo ===============================================================================
echo   Backend URL:      http://localhost:8000
echo   API Swagger Docs: http://localhost:8000/docs
echo   Frontend UI URL:  http://localhost:5173
echo ===============================================================================
echo.

:menu
echo Options:
echo   [1] Open Frontend Web App (http://localhost:5173)
echo   [2] Open API Interactive Docs (http://localhost:8000/docs)
echo   [3] Re-seed Database (Kora Retail Dataset)
echo   [4] Run Backend Pytest Suite (34 automated tests)
echo   [5] Stop all PayPilot services (Kill ports 8000, 5173)
echo   [6] Restart all PayPilot services
echo   [7] Exit this launcher (services keep running in their windows)
echo.
set "choice="
set /p choice="Select an option (1-7): "

if "%choice%"=="" goto menu
if "%choice%"=="1" goto opt_frontend
if "%choice%"=="2" goto opt_docs
if "%choice%"=="3" goto opt_seed
if "%choice%"=="4" goto opt_test
if "%choice%"=="5" goto opt_stop
if "%choice%"=="6" goto opt_restart
if "%choice%"=="7" goto opt_exit

echo Invalid selection. Please choose 1-7.
echo.
goto menu

:opt_frontend
start http://localhost:5173
goto menu

:opt_docs
start http://localhost:8000/docs
goto menu

:opt_seed
echo Re-seeding database...
%PYTHON_CMD% -m backend.app.data.seed
echo Done!
echo.
goto menu

:opt_test
echo Running pytest test suite...
%PYTHON_CMD% -m pytest backend/tests -v
echo.
goto menu

:opt_stop
echo Stopping PayPilot processes on ports 8000 and 5173...
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000,5173 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }" >nul 2>&1
taskkill /f /t /fi "WINDOWTITLE eq PayPilot Backend*" >nul 2>&1
taskkill /f /t /fi "WINDOWTITLE eq PayPilot Frontend*" >nul 2>&1
echo [OK] All services stopped.
echo.
goto menu

:opt_restart
echo Restarting PayPilot services...
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000,5173 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }" >nul 2>&1
taskkill /f /t /fi "WINDOWTITLE eq PayPilot Backend*" >nul 2>&1
taskkill /f /t /fi "WINDOWTITLE eq PayPilot Frontend*" >nul 2>&1
ping 127.0.0.1 -n 2 >nul 2>&1
start "PayPilot Backend (FastAPI - Port 8000)" /D "%SCRIPT_DIR%." cmd /k "title PayPilot Backend (FastAPI - Port 8000) && color 0A && echo Starting FastAPI Backend on http://localhost:8000 ... && %PYTHON_CMD% -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload"
start "PayPilot Frontend (Vite - Port 5173)" /D "%SCRIPT_DIR%frontend" cmd /k "title PayPilot Frontend (Vite - Port 5173) && color 0E && echo Starting Frontend UI on http://localhost:5173 ... && %FRONTEND_RUN%"
echo [OK] Services restarted.
echo.
goto menu

:opt_exit
echo Goodbye!
exit /b 0
