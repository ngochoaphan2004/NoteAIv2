@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set VPS_IP=180.93.54.122
set VPS_USER=root
set REMOTE_DIR=/opt/noteai

echo ====================================================================
echo  NoteAI.v2 - 1-Click Update Data ^& Assets to VPS: %VPS_IP%
echo ====================================================================

cd /d "%~dp0\.."

echo [1/3] Packing content/assets (Audio, PDF, APKG) and content/data (JSON Keys)...
tar -czf noteai_assets.tar.gz --exclude=__pycache__ --exclude=.git content/assets content/data
if %errorlevel% neq 0 (
    echo [ERROR] Dong goi assets that bai!
    pause
    exit /b %errorlevel%
)

echo [2/3] Uploading assets package to VPS (%VPS_IP%)...
scp -o StrictHostKeyChecking=no noteai_assets.tar.gz %VPS_USER%@%VPS_IP%:/tmp/noteai_assets.tar.gz
if %errorlevel% neq 0 (
    echo [ERROR] Upload len VPS that bai! Vui long kiem tra ket noi SSH.
    del /f /q noteai_assets.tar.gz 2>nul
    pause
    exit /b %errorlevel%
)

echo [3/3] Extracting on VPS and refreshing audio symlinks...
ssh -o StrictHostKeyChecking=no %VPS_USER%@%VPS_IP% "tar -xzf /tmp/noteai_assets.tar.gz -C %REMOTE_DIR%/ && rm -f /tmp/noteai_assets.tar.gz && mkdir -p %REMOTE_DIR%/public/assets && ln -sfn %REMOTE_DIR%/content/assets/audio %REMOTE_DIR%/public/assets/audio"

del /f /q noteai_assets.tar.gz 2>nul

echo ====================================================================
echo  UPDATE DATA ^& ASSETS SUCCESSFUL!
echo  Da dong bo toan bo Audio, PDF, Anki Deck va JSON dap an len VPS.
echo ====================================================================
pause
