@echo off
chcp 65001 >nul
echo ========================================
echo 🧹 清理專案快取檔案
echo ========================================
echo.

echo 正在清理 __pycache__ 資料夾...
for /d /r %%i in (__pycache__) do @if exist "%%i" rd /s /q "%%i"

echo 正在清理 .pyc 檔案...
del /s /q *.pyc 2>nul

echo 正在清理 .pyo 檔案...
del /s /q *.pyo 2>nul

echo.
echo ✅ 清理完成!
echo.
pause
