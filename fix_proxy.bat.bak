@echo off
title [Blog] Fix Git Proxy
set GIT=D:\Program Files\Git\cmd\git.exe
echo.
echo ============================================
echo    MU FENG BLOG - FIX GIT PROXY
echo ============================================
echo.
echo Run this ONLY if push fails with:
echo   "Failed to connect ... over proxy 127.0.0.1"
echo.
echo Removing dead proxy settings from global git config...
echo.
"%GIT%" config --global --unset http.proxy
"%GIT%" config --global --unset https.proxy
echo.
echo Done. Now double-click publish.bat
echo.
pause
