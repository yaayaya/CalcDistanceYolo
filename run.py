#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YOLO11 距離偵測系統 - 啟動腳本
從專案根目錄方便地啟動後端服務
"""

import os
import sys
from pathlib import Path

# 將 backend 目錄加入 Python 路徑
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# 切換工作目錄到 backend
os.chdir(backend_dir)

# 啟動 FastAPI 應用
if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("🚀 YOLO11 距離偵測系統")
    print("=" * 60)
    print(f"📂 工作目錄: {backend_dir}")
    print("🌐 啟動 FastAPI 服務...")
    print("=" * 60)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
