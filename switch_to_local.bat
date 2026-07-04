@echo off
REM ============================================================
REM Switch to LOCAL Configuration
REM ============================================================
echo.
echo ========================================
echo  MedicVista Retailer - Switch to LOCAL
echo ========================================
echo.

cd /d "%~dp0"

REM Backup current configs
if exist "config.ini" (
    echo [1/4] Backing up current config.ini...
    copy /Y "config.ini" "config.ini.backup" > nul
)

if exist "retailer_sync\retailer_sync_config.json" (
    echo [2/4] Backing up current retailer_sync_config.json...
    copy /Y "retailer_sync\retailer_sync_config.json" "retailer_sync\retailer_sync_config.json.backup" > nul
)

REM Switch to local configs
echo [3/4] Switching to LOCAL configuration...
copy /Y "config.local.ini" "config.ini" > nul
copy /Y "retailer_sync\retailer_sync_config.local.json" "retailer_sync\retailer_sync_config.json" > nul

echo [4/4] Verifying configuration...
echo.
echo ========================================
echo  Configuration Changed Successfully!
echo ========================================
echo.
echo  Mode: LOCAL
echo  Django ERP: http://127.0.0.1:8000
echo  Database: medicvista_retailer (localhost)
echo  Poll Interval: 10 seconds
echo.
echo ========================================
echo  What to do next:
echo ========================================
echo  1. Start Django ERP: python manage.py runserver
echo  2. Start Retailer App: python main.py
echo  3. Test connection: python retailer_sync\retailer_sync_runner.py --test-conn
echo.

pause
