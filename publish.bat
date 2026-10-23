@echo off
title [Blog] Publish Article
cd /d "%~dp0"
set GIT=C:\Program Files\Git\cmd\git.exe

echo.
echo ============================================
echo    MU FENG BLOG - PUBLISH
echo ============================================
echo.
echo [1/4] Checking changes...
"%GIT%" status --short
echo.
echo [2/4] Staging files...
"%GIT%" add .
echo.
echo [3/4] Committing...
"%GIT%" commit -m "update: %date% %time%"
if errorlevel 1 (
    echo.
    echo [!] Nothing to commit. Did you save the .md file?
    echo.
    pause
    exit /b 0
)
echo.
echo [4/4] Pushing to GitHub...
"%GIT%" push origin main
if errorlevel 1 (
    echo.
    echo [X] Push FAILED. Common causes:
    echo     - proxy problem: run fix_proxy.bat
    echo     - GitHub login required
    echo     Take a screenshot of the error above.
) else (
    echo.
    echo ============================================
    echo    SUCCESS! Wait 1 minute, then refresh:
    echo    https://mufeng168.top
    echo ============================================
)
echo.
pause
