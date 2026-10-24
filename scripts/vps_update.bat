@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set VPS_IP=180.93.54.122
set VPS_USER=root
set REMOTE_DIR=/opt/noteai

echo ====================================================================
echo  NoteAI.v2 - 1-Click Build and Update to VPS: %VPS_IP%
echo ====================================================================

cd /d "%~dp0\.."

set INCLUDE_ASSETS=0
if /i "%~1"=="--assets" set INCLUDE_ASSETS=1
if /i "%~1"=="all" set INCLUDE_ASSETS=1
if /i "%~1"=="with-assets" set INCLUDE_ASSETS=1
if /i "%~1"=="--no-assets" set INCLUDE_ASSETS=0
if /i "%~1"=="fast" set INCLUDE_ASSETS=0

if "%~1"=="" goto ASK_MODE
goto START_UPDATE

:ASK_MODE
echo.
echo Lua chon che do cap nhat len VPS:
echo   [1] Fast Mode (Mac dinh): Chi cap nhat Markdown, Plans va Code (Bo qua Data/Assets 112MB)
echo   [2] Full Mode: Cap nhat Day Du ca Data ^& Assets (Audio, PDF, JSON...)
echo.
set /p "USER_CHOICE=Nhap lua chon [1 hoac 2, Enter=1]: "
if "%USER_CHOICE%"=="2" set INCLUDE_ASSETS=1

:START_UPDATE

echo.
if "!INCLUDE_ASSETS!"=="1" (
    echo [MODE] Full Mode: Se cap nhat toan bo Code, Content, Plans va Data/Assets
) else (
    echo [MODE] Fast Mode: Chi cap nhat Markdown, Plans va Code, khong zip data/assets
)
echo.

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

if "!INCLUDE_ASSETS!"=="1" (
    echo [3/5] Compressing FULL update package including data and assets...
    tar -czf noteai_update.tar.gz --exclude=__pycache__ --exclude=.pytest_cache --exclude=node_modules --exclude=.quartz-cache --exclude=.git --exclude=data/cambridge18_images backend content templates frontend/dist public scripts quartz quartz.config.ts quartz.layout.ts package.json package-lock.json tsconfig.json
) else (
    echo [3/5] Compressing FAST update package excluding heavy data and assets...
    tar -czf noteai_update.tar.gz --exclude=__pycache__ --exclude=.pytest_cache --exclude=node_modules --exclude=.quartz-cache --exclude=.git --exclude=content/assets --exclude=content/data --exclude=data --exclude=public/assets/audio backend content templates frontend/dist public scripts quartz quartz.config.ts quartz.layout.ts package.json package-lock.json tsconfig.json
)

echo [4/5] Cleaning old compiled folders ^& auto-backing up VPS content...
ssh -o StrictHostKeyChecking=no %VPS_USER%@%VPS_IP% "rm -rf %REMOTE_DIR%/frontend/dist %REMOTE_DIR%/public && mkdir -p %REMOTE_DIR%/backups && tar -czf %REMOTE_DIR%/backups/content_before_update_$(date +%%Y%%m%%d_%%H%%M%%S).tar.gz --exclude='content/assets/audio' -C %REMOTE_DIR% content 2>/dev/null && (ls -dt %REMOTE_DIR%/backups/* 2>/dev/null | tail -n +11 | xargs rm -rf 2>/dev/null || true)"

echo [5/5] Uploading to VPS and restarting services...
scp -o StrictHostKeyChecking=no noteai_update.tar.gz %VPS_USER%@%VPS_IP%:/tmp/noteai_update.tar.gz
if %errorlevel% neq 0 (
    echo [ERROR] Upload to VPS failed! Please check SSH connection.
    del /f /q noteai_update.tar.gz 2>nul
    pause
    exit /b %errorlevel%
)

ssh -o StrictHostKeyChecking=no %VPS_USER%@%VPS_IP% "tar -xzf /tmp/noteai_update.tar.gz -C %REMOTE_DIR%/ --overwrite && rm -f /tmp/noteai_update.tar.gz && cd %REMOTE_DIR% && bash scripts/update_vps.sh"

del /f /q noteai_update.tar.gz 2>nul

echo ====================================================================
echo  UPDATE SUCCESSFUL!
echo  Cac service dang chay an toan tren localhost (127.0.0.1):
echo  - NoteAI Unified Gateway (React SPA + API + Garden): http://127.0.0.1:8000
echo  - PostgreSQL (Local): 127.0.0.1:5432
echo  - Qdrant Vector DB:   127.0.0.1:6333
echo  Truy cap cong cong an toan qua Cloudflare Tunnel (tro ve http://127.0.0.1:8000)
echo ====================================================================
pause
