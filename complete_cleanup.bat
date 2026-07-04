@echo off
echo.
echo ============================================
echo  COMPLETE CLEANUP AND LOCAL RESET
echo ============================================
echo.

cd /d "%~dp0"

echo [1/7] Killing ALL Python processes...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM pythonw.exe /T >nul 2>&1
timeout /t 3 >nul

echo [2/7] Deleting Python cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
del /s /q *.pyc >nul 2>&1
echo Done

echo [3/7] Deleting SQLite cache databases...
if exist "retailer_request_cache.db" del /f "retailer_request_cache.db" >nul 2>&1
if exist "retailer_sync\retailer_request_cache.db" del /f "retailer_sync\retailer_request_cache.db" >nul 2>&1
if exist "retailer_sync\retailer_sync.log" del /f "retailer_sync\retailer_sync.log" >nul 2>&1
echo Done

echo [4/7] Backing up old config...
if exist "config.ini" copy /Y "config.ini" "config.ini.backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%" >nul 2>&1

echo [5/7] Force writing LOCAL configuration...
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
echo Done

echo [6/7] Verifying configuration...
python debug_config.py
echo.

echo [7/7] Final check...
findstr /C:"environment = LOCAL" config.ini >nul
if errorlevel 1 (
    echo [ERROR] Config verification failed!
    pause
    exit /b 1
) else (
    echo [OK] Config is LOCAL
)

echo.
echo ============================================
echo  CLEANUP COMPLETE!
echo ============================================
echo.
echo Configuration:
echo   Database: medicvista_retailer
echo   ERP DB:   pharma_db
echo   Server:   http://127.0.0.1:8000
echo   Mode:     LOCAL
echo.
echo ============================================
echo  IMPORTANT: Start Django ERP First!
echo ============================================
echo.
echo 1. Open NEW terminal
echo 2. cd to Django project folder
echo 3. python manage.py runserver
echo.
echo Then start this application:
echo 4. python main.py
echo.
pause
