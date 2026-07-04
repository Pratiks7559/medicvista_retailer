@echo off
REM ============================================================
REM Switch to CLOUD Configuration
REM ============================================================
echo.
echo ========================================
echo  MedicVista Retailer - Switch to CLOUD
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

REM Switch to cloud configs
echo [3/4] Switching to CLOUD configuration...
copy /Y "config.cloud.ini" "config.ini" > nul
copy /Y "retailer_sync\retailer_sync_config.cloud.json" "retailer_sync\retailer_sync_config.json" > nul

echo [4/4] Verifying configuration...
echo.
echo ========================================
echo  Configuration Changed Successfully!
echo ========================================
echo.
echo  Mode: CLOUD
echo  Django ERP: http://medicvistapharma.com
echo  Database: medicvista_retailer (localhost)
echo  Poll Interval: 60 seconds
echo.
echo ========================================
echo  What to do next:
echo ========================================
echo  1. Test connection: python retailer_sync\retailer_sync_runner.py --test-conn
echo  2. Start Retailer App: python main.py
echo  3. Check status in Django admin
echo.
echo ========================================
echo  IMPORTANT:
echo ========================================
echo  Make sure medicvistapharma.com is accessible
echo  and Django ERP is deployed on cloud!
echo.

pause
