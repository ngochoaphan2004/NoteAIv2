@echo off
setlocal

set VPS_IP=180.93.54.122
set VPS_USER=root
set REMOTE_DIR=/opt/noteai

echo ====================================================================
echo  NoteAI.v2 - 1-Click Build and Update to VPS: %VPS_IP%
echo ====================================================================

cd /d "%~dp0\.."

echo [0/5] Syncing daily plans to today...
python -X utf8 -c "import sys; sys.path.insert(0, 'backend'); from app.services.plan_service import plan_service; plan_service.sync_all_plans()" 2>nul

echo [1/5] Building Frontend React SPA...
cd frontend
call npm run build
if %errorlevel% neq 0 (
    echo [ERROR] Build Frontend failed!
    pause
    exit /b %errorlevel%
)
cd ..

echo [2/5] Building Quartz Digital Garden...
call npx quartz build
if %errorlevel% neq 0 (
    echo [ERROR] Build Quartz failed!
    pause
    exit /b %errorlevel%
)

echo [3/5] Compressing update package (excluding heavy audio & build caches)...
tar -czf noteai_update.tar.gz --exclude=__pycache__ --exclude=.pytest_cache --exclude=node_modules --exclude=.quartz-cache --exclude=.git --exclude=content/assets/audio --exclude=public/assets/audio backend content frontend/dist public scripts quartz quartz.config.ts quartz.layout.ts package.json package-lock.json tsconfig.json

echo [4/5] Cleaning old compiled folders (frontend/dist & public) on VPS before upload...
ssh -o StrictHostKeyChecking=no %VPS_USER%@%VPS_IP% "rm -rf %REMOTE_DIR%/frontend/dist %REMOTE_DIR%/public"

echo [5/5] Uploading to VPS and restarting services...
scp -o StrictHostKeyChecking=no noteai_update.tar.gz %VPS_USER%@%VPS_IP%:/tmp/noteai_update.tar.gz
if %errorlevel% neq 0 (
    echo [ERROR] Upload to VPS failed! Please check SSH connection.
    pause
    exit /b %errorlevel%
)

ssh -o StrictHostKeyChecking=no %VPS_USER%@%VPS_IP% "tar -xzf /tmp/noteai_update.tar.gz -C %REMOTE_DIR%/ --overwrite && rm -f /tmp/noteai_update.tar.gz && cd %REMOTE_DIR% && bash scripts/update_vps.sh"

del /f /q noteai_update.tar.gz 2>nul

echo ====================================================================
echo  UPDATE SUCCESSFUL!
echo  Web SPA:        http://%VPS_IP%/
echo  Digital Garden: http://%VPS_IP%:8088/
echo  API Swagger:    http://%VPS_IP%/docs
echo ====================================================================
pause
