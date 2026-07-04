@echo off
REM ============================================================
REM MedicVista Retailer - Configuration Switch Menu
REM ============================================================
:MENU
cls
echo.
echo ========================================================
echo          MedicVista Retailer Configuration
echo ========================================================
echo.
echo  Choose Configuration Mode:
echo.
echo  1. LOCAL    - Local DB + Local Django Server
echo                Database: medicvista_retailer
echo                ERP DB:   pharma_db
echo                Server:   http://127.0.0.1:8000
echo.
echo  2. CLOUD    - Local DB + Cloud Django Server
echo                Database: medicvista_retailer
echo                ERP DB:   medicvistapharma_db
echo                Server:   https://medicvista.godaddysites.com
echo.
echo  3. VERIFY   - Check current configuration
echo.
echo  4. EXIT     - Exit this menu
echo.
echo ========================================================
echo.

set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" goto LOCAL
if "%choice%"=="2" goto CLOUD
if "%choice%"=="3" goto VERIFY
if "%choice%"=="4" goto EXIT

echo.
echo Invalid choice! Please try again.
timeout /t 2 >nul
goto MENU

:LOCAL
cls
echo.
echo Switching to LOCAL mode...
echo.
cd /d "%~dp0"

REM Force overwrite config.ini with fresh LOCAL config
echo Writing LOCAL configuration to config.ini...
(
echo # ============================================================
echo # MedicVista Retailer - LOCAL Configuration
echo # ============================================================
echo # Retailer App Database: medicvista_retailer ^(Local^)
echo # Django ERP Database: pharma_db ^(Local - localhost:8000^)
echo # ============================================================
echo.
echo [database]
echo # Retailer app's own database
echo host = localhost
echo port = 3306
echo name = medicvista_retailer
echo user = root
echo password = Pratik@123
echo.
echo [erp_database]
echo # Django ERP database for retailer_request sync
echo host = localhost
echo port = 3306
echo name = pharma_db
echo user = root
echo password = Pratik@123
echo.
echo [retailer1]
echo retailer_id = 1
echo store_name = BSL Pharmacy
echo retailer_code = RTL001
echo.
echo [retailer2]
echo retailer_id = 2
echo store_name = MedPlus Retail
echo retailer_code = RTL002
echo.
echo [retailer3]
echo retailer_id = 3
echo store_name = Apollo Pharmacy
echo retailer_code = RTL003
echo.
echo [retailer4]
echo retailer_id = 4
echo store_name = Wellness Forever
echo retailer_code = RTL004
echo.
echo [sync]
echo poll_seconds = 10
echo.
echo [mode]
echo environment = LOCAL
echo description = Local with pharma_db for retailer requests
) > config.ini

REM Clear cache
if exist "retailer_request_cache.db" del /f "retailer_request_cache.db" >nul 2>&1
if exist "retailer_sync\retailer_request_cache.db" del /f "retailer_sync\retailer_request_cache.db" >nul 2>&1

echo [OK] Configuration: LOCAL
echo      Database: medicvista_retailer
echo      ERP DB:   pharma_db
echo      Server:   http://127.0.0.1:8000
echo.
echo Next: Restart application (python main.py)
echo.
pause
goto MENU

:CLOUD
cls
echo.
echo Switching to CLOUD mode...
echo.
cd /d "%~dp0"

REM Backup current config
if exist "config.ini" (
    copy /Y "config.ini" "config.ini.local_backup" > nul
)

REM Force overwrite with CLOUD config
echo Writing CLOUD configuration to config.ini...
copy /Y "config_deploy.ini" "config.ini" > nul

REM Clear cache
if exist "retailer_request_cache.db" del /f "retailer_request_cache.db" >nul 2>&1
if exist "retailer_sync\retailer_request_cache.db" del /f "retailer_sync\retailer_request_cache.db" >nul 2>&1

echo [OK] Configuration: CLOUD
echo      Database: medicvista_retailer
echo      ERP DB:   medicvistapharma_db
echo      Server:   https://medicvista.godaddysites.com
echo.
echo WARNING: Using PRODUCTION ERP database!
echo.
echo Next: Restart application (python main.py)
echo.
pause
goto MENU

:VERIFY
cls
echo.
echo ========================================================
echo          Current Configuration
echo ========================================================
echo.
cd /d "%~dp0"
if exist "config.ini" (
    echo Main Database:
    findstr /C:"name =" config.ini | findstr /V /C:"#" | findstr /V /C:"erp"
    echo.
    echo ERP Database:
    findstr /C:"[erp_database]" config.ini >nul 2>&1
    if errorlevel 1 (
        echo   Not configured ^(single database mode^)
    ) else (
        findstr /C:"name =" config.ini | findstr /V /C:"#" | findstr "erp" >nul 2>&1
        if not errorlevel 1 (
            findstr /C:"name =" config.ini | findstr "erp"
        ) else (
            echo   pharma_db ^(default^)
        )
    )
    echo.
    echo Environment:
    findstr /C:"environment =" config.ini | findstr /V /C:"#"
    echo.
) else (
    echo [ERROR] config.ini not found!
)
echo.
echo ========================================================
pause
goto MENU

:EXIT
echo.
echo Exiting...
exit /b 0
