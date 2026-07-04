@echo off
REM ============================================================
REM Check Current Configuration
REM ============================================================
echo.
echo ========================================
echo  MedicVista Retailer - Current Config
echo ========================================
echo.

cd /d "%~dp0"

REM Check main config
echo [Checking config.ini...]
if exist "config.ini" (
    findstr /C:"environment" config.ini > nul
    if errorlevel 1 (
        echo  Status: UNKNOWN (old config format)
    ) else (
        echo  Config file: config.ini
        findstr /C:"environment" /C:"description" config.ini
    )
) else (
    echo  ERROR: config.ini not found!
)

echo.
echo [Checking retailer_sync_config.json...]
if exist "retailer_sync\retailer_sync_config.json" (
    findstr /C:"server_mode" /C:"server_url" retailer_sync\retailer_sync_config.json
) else (
    echo  ERROR: retailer_sync_config.json not found!
)

echo.
echo ========================================
echo  Available Configurations:
echo ========================================
echo  1. LOCAL  - Use: switch_to_local.bat
echo  2. CLOUD  - Use: switch_to_cloud.bat
echo.

REM Test connection
echo ========================================
echo  Test Connection? (y/n)
echo ========================================
set /p test="Enter choice: "

if /i "%test%"=="y" (
    echo.
    echo Testing connection...
    python retailer_sync\retailer_sync_runner.py --test-conn
)

echo.
pause
