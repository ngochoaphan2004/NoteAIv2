@echo off
setlocal

set VPS_IP=180.93.54.122
set VPS_USER=root
set REMOTE_DIR=/opt/noteai

echo ====================================================================
echo  NoteAI.v2 - 1-Click Build and Update to VPS: %VPS_IP%
echo ====================================================================

cd /d "%~dp0\.."

echo [1/4] Building Frontend React SPA...
cd frontend
call npm run build
if %errorlevel% neq 0 (
    echo [ERROR] Build Frontend failed!
    pause
    exit /b %errorlevel%
)
cd ..

echo [2/4] Building Quartz Digital Garden...
call npx quartz build
if %errorlevel% neq 0 (
    echo [ERROR] Build Quartz failed!
    pause
    exit /b %errorlevel%
)

echo [3/4] Compressing update package...
tar -czf noteai_update.tar.gz --exclude=__pycache__ --exclude=.pytest_cache backend content frontend/dist public scripts

echo [4/4] Uploading to VPS and restarting services...
echo Please enter VPS password when prompted.
scp noteai_update.tar.gz %VPS_USER%@%VPS_IP%:/tmp/noteai_update.tar.gz

ssh %VPS_USER%@%VPS_IP% "tar -xzf /tmp/noteai_update.tar.gz -C %REMOTE_DIR%/ && rm -f /tmp/noteai_update.tar.gz && cd %REMOTE_DIR% && bash scripts/update_vps.sh"

del /f /q noteai_update.tar.gz 2>nul

echo ====================================================================
echo  UPDATE SUCCESSFUL!
echo  Web SPA:        http://%VPS_IP%/
echo  Digital Garden: http://%VPS_IP%:8088/
echo  API Swagger:    http://%VPS_IP%/docs
echo ====================================================================
pause
