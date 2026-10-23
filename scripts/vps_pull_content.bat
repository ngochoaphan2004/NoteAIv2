@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set VPS_IP=180.93.54.122
set VPS_USER=root
set REMOTE_DIR=/opt/noteai

echo ====================================================================
echo  NoteAI.v2 - 1-Click Pull Content va Bai Thi Tu VPS: %VPS_IP%
echo ====================================================================

cd /d "%~dp0\.."

python -X utf8 scripts\_py_\pull_server_content.py %*
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Qua trinh keo du lieu tu VPS gap su co! Vui long kiem tra lai.
    pause
    exit /b %errorlevel%
)

echo.
pause
