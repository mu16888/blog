@echo off
chcp 936 >nul
title [沐风博客] 本地预览
cd /d "E:\workbuddy工作台\mufeng-blog"

echo.
echo ============================================
echo    沐风博客 - 本地预览
echo ============================================
echo.
echo 浏览器打开 http://localhost:1313
echo 左边改文件，右边自动刷新
echo.
echo 要停止预览，按 Ctrl + C 或直接关掉这个窗口
echo.

"E:\workbuddy工作台\mufeng-blog\tools\hugo.exe" server -s "E:\workbuddy工作台\mufeng-blog" --bind 0.0.0.0
