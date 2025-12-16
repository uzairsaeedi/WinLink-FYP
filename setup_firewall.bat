@echo off
title WinLink Firewall & Port Setup

cls
echo.
echo ========================================
echo   WinLink Firewall & Port Setup
echo ========================================
echo.
echo This script will:
echo   1. Clean up any port conflicts
echo   2. Configure Windows Firewall rules
echo   3. Prepare system for Master/Worker roles
echo.
echo Administrator rights required
echo Run on BOTH Master and Worker PCs
echo ========================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Administrator rights required!
    echo.
    echo Please right-click this file and select
    echo "Run as administrator" to continue.
    echo.
    pause
    exit /b 1
)

echo ========================================
echo STEP 1: PORT CLEANUP
echo ========================================
echo.
echo Cleaning up any existing port conflicts...
echo This ensures smooth role switching.
echo.

echo [1/3] Stopping any running Python processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1

echo [2/3] Releasing WinLink ports (3000-3100, 5555-5560)...
timeout /t 2 /nobreak >nul

REM Kill processes using Worker ports
for /L %%p in (3000,1,3100) do (
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr :%%p ^| findstr LISTENING') do (
        taskkill /F /PID %%a >nul 2>&1
    )
)

REM Kill processes using Master ports
for /L %%p in (5555,1,5560) do (
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr :%%p ^| findstr LISTENING') do (
        taskkill /F /PID %%a >nul 2>&1
    )
)

echo [3/3] Waiting for ports to be released...
timeout /t 2 /nobreak >nul

echo.
echo Port cleanup complete!
echo.

echo ========================================
echo STEP 2: FIREWALL CONFIGURATION
echo ========================================
echo.

REM Remove any existing WinLink rules first
netsh advfirewall firewall delete rule name="WinLink" >nul 2>&1
netsh advfirewall firewall delete rule name="WinLink Worker" >nul 2>&1
netsh advfirewall firewall delete rule name="WinLink Master" >nul 2>&1
netsh advfirewall firewall delete rule name="WinLink Discovery" >nul 2>&1

echo [1/8] Adding Worker inbound TCP rules (ports 3000-3100)...
netsh advfirewall firewall add rule name="WinLink Worker" dir=in action=allow protocol=TCP localport=3000-3100 enable=yes profile=any

echo [2/8] Adding Worker outbound TCP rules (ports 3000-3100)...
netsh advfirewall firewall add rule name="WinLink Worker" dir=out action=allow protocol=TCP remoteport=3000-3100 enable=yes profile=any

echo [3/8] Adding Master inbound TCP rules (ports 5555-5560)...
netsh advfirewall firewall add rule name="WinLink Master" dir=in action=allow protocol=TCP localport=5555-5560 enable=yes profile=any

echo [4/8] Adding Master outbound TCP rules (ports 5555-5560)...
netsh advfirewall firewall add rule name="WinLink Master" dir=out action=allow protocol=TCP remoteport=5555-5560 enable=yes profile=any

echo [5/8] Adding Discovery inbound UDP rule (port 5000)...
netsh advfirewall firewall add rule name="WinLink Discovery" dir=in action=allow protocol=UDP localport=5000 enable=yes profile=any

echo [6/8] Adding Discovery outbound UDP rule (port 5000)...
netsh advfirewall firewall add rule name="WinLink Discovery" dir=out action=allow protocol=UDP remoteport=5000 enable=yes profile=any

echo [7/8] Adding general TCP inbound rule...
netsh advfirewall firewall add rule name="WinLink" dir=in action=allow protocol=TCP enable=yes profile=any

echo [8/8] Adding general TCP outbound rule...
netsh advfirewall firewall add rule name="WinLink" dir=out action=allow protocol=TCP enable=yes profile=any

echo.
echo ========================================
echo SETUP COMPLETE!
echo ========================================
echo.
echo [✓] Ports cleaned and released
echo [✓] Firewall rules configured
echo [✓] System ready for WinLink
echo.
echo You can now run WinLink in either role:
echo.
echo   Master PC:  python main.py  (select Master)
echo   Worker PC:  python main.py  (select Worker)
echo.
echo Or use the launcher:
echo   python launch_enhanced.py --role master
echo   python launch_enhanced.py --role worker
echo.
echo ========================================
echo NOTES:
echo ========================================
echo.
echo - Run this script on BOTH Master and Worker PCs
echo - If switching roles on same PC, just run this again
echo - Firewall rules persist across reboots
echo - Port cleanup happens automatically each run
echo.
pause
