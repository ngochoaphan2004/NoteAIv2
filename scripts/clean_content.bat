@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set VPS_IP=180.93.54.122
set VPS_USER=root
set REMOTE_DIR=/opt/noteai

echo ====================================================================
echo  NoteAI.v2 - Clean Server Content va Files: %VPS_IP%
echo ====================================================================

echo.
echo [!] CANH BAO: Script nay se xoa du lieu tren server %VPS_IP%
echo     - Giu nguyen 100%%: venv, node_modules, package*.json, .env (XOA ca content va audio)
echo.

ssh -t -o StrictHostKeyChecking=no %VPS_USER%@%VPS_IP% "bash %REMOTE_DIR%/clean_content.sh"
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Ket noi hoac thuc thi tren server gap loi!
    pause
    exit /b %errorlevel%
)

echo.
pause
