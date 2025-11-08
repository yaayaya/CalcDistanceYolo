#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YOLO11 距離偵測 FastAPI 主應用
"""

import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from app.services.detector import YOLODetectorService
from app.services.connection_manager import ConnectionManager
from app.api import websocket, frontend


# 解決 OpenMP 函式庫衝突問題
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'


# 全域服務實例
detector_service: YOLODetectorService = None
connection_manager: ConnectionManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    應用生命週期管理
    啟動時初始化服務,關閉時清理資源
    """
    global detector_service, connection_manager
    
    # === 啟動時 ===
    print("🚀 正在啟動 YOLO11 距離偵測服務...")
    
    # 初始化服務
    detector_service = YOLODetectorService()
    connection_manager = ConnectionManager(detector_service)
    
    # 初始化 API 端點的服務依賴
    websocket.init_websocket_services(detector_service, connection_manager)
    frontend.init_frontend_services(detector_service)
    
    print("✅ 服務啟動完成!")
    print("📍 後台管理介面: http://localhost:8000/admin")
    print("📍 API 文件: http://localhost:8000/docs")
    
    yield
    
    # === 關閉時 ===
    print("🛑 正在關閉服務...")
    
    if detector_service and detector_service.is_running:
        await detector_service.stop_detection()
    
    if connection_manager:
        await connection_manager.disconnect_all()
    
    print("👋 服務已關閉")


# 建立 FastAPI 應用
app = FastAPI(
    title="YOLO11 距離偵測 API",
    description="基於 YOLO11n 的即時人體距離偵測系統,提供 WebSocket 即時串流和 RESTful API",
    version="1.0.0",
    lifespan=lifespan
)


# === 註冊路由 ===
app.include_router(websocket.router)
app.include_router(frontend.router)


# === 靜態檔案服務 ===
# 後台管理介面
app.mount("/admin", StaticFiles(directory="../frontend", html=True), name="admin")

# Flur 頁面服務
from fastapi.responses import FileResponse

@app.get("/flur")
async def flur_page():
    """FlurPaint 互動藝術裝置展示頁面"""
    return FileResponse("../frontend/flur.html")

@app.get("/flur-admin")
async def flur_admin_page():
    """FlurPaint 後台管理頁面"""
    return FileResponse("../frontend/flur_admin.html")


# === 根路徑 ===
@app.get("/")
async def root():
    """
    根路徑 - 服務資訊
    """
    return {
        "service": "YOLO11 Distance Detection API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "flur": "/flur",
            "flur_admin": "/flur-admin",
            "admin": "/admin",
            "docs": "/docs",
            "websocket_detection": "/ws/detection",
            "websocket_live": "/ws/live",
            "websocket_flur": "/ws/flur",
            "api": "/api"
        }
    }


# === 健康檢查 ===
@app.get("/health")
async def health():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "detector_running": detector_service.is_running if detector_service else False
    }


if __name__ == "__main__":
    import uvicorn
    
    # 開發環境啟動
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
