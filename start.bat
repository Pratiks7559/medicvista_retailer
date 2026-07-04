@echo off
REM ============================================================
REM MedicVista Retailer - Smart Startup
REM ============================================================
REM Automatically clears cache and starts application
REM ============================================================

cd /d "%~dp0"

echo.
echo Starting MedicVista Retailer...
echo.

REM Clear SQLite cache automatically
if exist "retailer_request_cache.db" del /f "retailer_request_cache.db" >nul 2>&1
if exist "retailer_sync\retailer_request_cache.db" del /f "retailer_sync\retailer_request_cache.db" >nul 2>&1

REM Check config
if not exist "config.ini" (
    echo [ERROR] config.ini not found!
    echo Run switch_config.bat first to setup configuration.
    pause
    exit /b 1
)

REM Show current mode
findstr /C:"environment = LOCAL" config.ini >nul
if not errorlevel 1 (
    echo [INFO] Mode: LOCAL
    echo [INFO] Server: http://127.0.0.1:8000
) else (
    findstr /C:"environment = CLOUD" config.ini >nul
    if not errorlevel 1 (
        echo [INFO] Mode: CLOUD
        echo [INFO] Server: https://medicvista.godaddysites.com
    )
)

echo.

REM Start application
python main.py

REM If error, show message
if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with error
    pause
)
