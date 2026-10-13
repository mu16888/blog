@echo off
chcp 936 >nul
title [Blog] Fix Git Proxy
echo.
echo ============================================
echo    MU FENG BLOG - FIX GIT PROXY
echo ============================================
echo.
echo Run this ONLY if push fails with:
echo   "Failed to connect ... over proxy 127.0.0.1"
echo.
echo This removes the dead proxy setting from
echo your global git config.
echo.

"%ProgramFiles%\Git\cmd\git.exe" config --global --unset http.proxy
"%ProgramFiles%\Git\cmd\git.exe" config --global --unset https.proxy

echo.
echo Done. Now double-click: publish.bat
echo.
pause
