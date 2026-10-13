@echo off
title [Blog] Local Preview
cd /d "%~dp0"

echo.
echo ============================================
echo    MU FENG BLOG - LOCAL PREVIEW
echo ============================================
echo.
echo Open in browser:  http://localhost:1313
echo Edit .md files, browser refreshes automatically.
echo.
echo To stop: press Ctrl + C, or just close this window.
echo.
"%~dp0tools\hugo.exe" server -s "%~dp0" --bind 0.0.0.0
