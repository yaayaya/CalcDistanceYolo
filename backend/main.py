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
from app.api import websocket, frontend, admin_api


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
    print("📍 播放頁面: http://localhost:8000/player.html")
    print("📍 後台管理介面: http://localhost:8000/admin.html")
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
app.include_router(admin_api.router)


# === 靜態檔案服務 (前端頁面) ===
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")


# === 根路徑 ===
@app.get("/")
async def root():
    """
    根路徑 - 重定向到 API 文件
    """
    return {
        "service": "YOLO11 Distance Detection API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "player": "/player.html",
            "admin": "/admin.html",
            "docs": "/docs",
            "websocket_detection": "/ws/detection",
            "websocket_live": "/ws/live",
            "api": "/api",
            "admin_api": "/api/admin"
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
