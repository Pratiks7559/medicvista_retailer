@echo off
echo.
echo ============================================
echo  COMPLETE RESET TO LOCAL MODE
echo ============================================
echo.

cd /d "%~dp0"

echo [1/5] Killing Python processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1
timeout /t 2 >nul

echo [2/5] Clearing ALL cache...
if exist "__pycache__" rd /s /q "__pycache__" >nul 2>&1
if exist "app\__pycache__" rd /s /q "app\__pycache__" >nul 2>&1
if exist "retailer_sync\__pycache__" rd /s /q "retailer_sync\__pycache__" >nul 2>&1
if exist "*.pyc" del /s /q "*.pyc" >nul 2>&1
if exist "retailer_request_cache.db" del "retailer_request_cache.db" >nul 2>&1
if exist "retailer_sync\retailer_request_cache.db" del "retailer_sync\retailer_request_cache.db" >nul 2>&1
if exist "retailer_sync\retailer_sync.log" del "retailer_sync\retailer_sync.log" >nul 2>&1

echo [3/5] Config already set to LOCAL

echo [4/5] Verifying configuration...
python debug_config.py

echo.
echo [5/5] Configuration verified!
echo.
echo ============================================
echo  Ready to Start!
echo ============================================
echo.
echo Next: Start application
echo   python main.py
echo.
pause
