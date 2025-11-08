@echo off
chcp 65001 > nul
echo ========================================
echo 🎨 FlurPaint 互動藝術裝置
echo ========================================
echo.
echo 正在啟動後端服務...
echo.

cd backend
python main.py

pause
