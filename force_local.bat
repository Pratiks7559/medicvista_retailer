@echo off
echo.
echo ============================================
echo  FORCE LOCAL MODE - Complete Reset
echo ============================================
echo.

cd /d "%~dp0"

echo [1/5] Stopping any running Python processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1
timeout /t 2 >nul

echo [2/5] Clearing cache files...
if exist "retailer_request_cache.db" del "retailer_request_cache.db" >nul 2>&1
if exist "retailer_sync\retailer_request_cache.db" del "retailer_sync\retailer_request_cache.db" >nul 2>&1
if exist "retailer_sync\retailer_sync.log" del "retailer_sync\retailer_sync.log" >nul 2>&1

echo [3/5] Backing up current config...
if exist "config.ini" copy /Y "config.ini" "config.ini.old" >nul

echo [4/5] Forcing LOCAL configuration...
echo # ============================================================ > config.ini
echo # MedicVista Retailer - LOCAL Configuration >> config.ini
echo # ============================================================ >> config.ini
echo # Retailer App Database: medicvista_retailer (Local) >> config.ini
echo # Django ERP Database: pharma_db (Local - localhost:8000) >> config.ini
echo # ============================================================ >> config.ini
echo. >> config.ini
echo [database] >> config.ini
echo # Retailer app's own database >> config.ini
echo host = localhost >> config.ini
echo port = 3306 >> config.ini
echo name = medicvista_retailer >> config.ini
echo user = root >> config.ini
echo password = Pratik@123 >> config.ini
echo. >> config.ini
echo [erp_database] >> config.ini
echo # Django ERP database for retailer_request sync >> config.ini
echo host = localhost >> config.ini
echo port = 3306 >> config.ini
echo name = pharma_db >> config.ini
echo user = root >> config.ini
echo password = Pratik@123 >> config.ini
echo. >> config.ini
echo [retailer1] >> config.ini
echo retailer_id = 1 >> config.ini
echo store_name = BSL Pharmacy >> config.ini
echo retailer_code = RTL001 >> config.ini
echo. >> config.ini
echo [retailer2] >> config.ini
echo retailer_id = 2 >> config.ini
echo store_name = MedPlus Retail >> config.ini
echo retailer_code = RTL002 >> config.ini
echo. >> config.ini
echo [retailer3] >> config.ini
echo retailer_id = 3 >> config.ini
echo store_name = Apollo Pharmacy >> config.ini
echo retailer_code = RTL003 >> config.ini
echo. >> config.ini
echo [retailer4] >> config.ini
echo retailer_id = 4 >> config.ini
echo store_name = Wellness Forever >> config.ini
echo retailer_code = RTL004 >> config.ini
echo. >> config.ini
echo [sync] >> config.ini
echo poll_seconds = 10 >> config.ini
echo. >> config.ini
echo [mode] >> config.ini
echo environment = LOCAL >> config.ini
echo description = Local with pharma_db for retailer requests >> config.ini

echo [5/5] Verifying configuration...
echo.
echo ============================================
echo  Configuration Updated!
echo ============================================
echo.
echo  Mode: LOCAL
echo  Database: medicvista_retailer
echo  ERP Database: pharma_db
echo  Server: http://127.0.0.1:8000
echo.
echo ============================================
echo  Next Steps:
echo ============================================
echo  1. Start Django ERP (if not running):
echo     python manage.py runserver
echo.
echo  2. Start Retailer App in NEW terminal:
echo     python main.py
echo.
echo  3. Login and check Retailer Requests screen
echo     Should show: http://127.0.0.1:8000
echo.
pause
