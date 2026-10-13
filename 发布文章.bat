@echo off
chcp 936 >nul
title [Blog] Publish Article - One Click
cd /d "%~dp0"

echo.
echo ============================================
echo    MU FENG BLOG - PUBLISH
echo ============================================
echo.
echo Double-click this file to publish.
echo Chinese text is intentionally avoided so that
echo cmd.exe will not break the line.
echo.

echo [1/4] Checking changes...
"%ProgramFiles%\Git\cmd\git.exe" status --short
echo.

echo [2/4] Staging...
"%ProgramFiles%\Git\cmd\git.exe" add .
echo.

echo [3/4] Committing...
"%ProgramFiles%\Git\cmd\git.exe" commit -m "update: %date% %time%"
if errorlevel 1 (
    echo.
    echo [!] Nothing to commit. Did you save the .md file?
    echo.
    pause
    exit /b 0
)
echo.

echo [4/4] Pushing to GitHub...
"%ProgramFiles%\Git\cmd\git.exe" push origin main
if errorlevel 1 (
    echo.
    echo [X] Push FAILED. Common causes:
    echo     - proxy problem: run  fix-proxy.bat
    echo     - need GitHub login
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
