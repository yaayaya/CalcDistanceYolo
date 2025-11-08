#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FlurPaint 系統測試腳本
測試配置載入、API端點和 WebSocket 連線
"""

import sys
import asyncio
import requests
import json
from pathlib import Path

# 添加 backend 路徑
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.utils.config_loader import load_project_config, load_sensor_config


def test_config_loading():
    """測試配置檔案載入"""
    print("=" * 60)
    print("📋 測試 1: 配置檔案載入")
    print("=" * 60)
    
    try:
        # 測試 project_config
        project_config = load_project_config()
        print("✅ project_config.json 載入成功")
        print(f"   - YOLO 設備: {project_config['yolo_device']['device']}")
        print(f"   - 最小解析度: {project_config['blur_control']['min_resolution_width']}px")
        print(f"   - 最大解析度: {project_config['blur_control']['max_resolution_width']}px")
        
        # 測試 sensor_config
        sensor_config = load_sensor_config()
        print("✅ sensor_config.json 載入成功")
        print(f"   - 攝影機來源: {sensor_config['camera']['source']}")
        print(f"   - 攝影機解析度: {sensor_config['camera']['width']}x{sensor_config['camera']['height']}")
        
        return True
    except Exception as e:
        print(f"❌ 配置載入失敗: {e}")
        return False


def test_api_endpoints():
    """測試 API 端點"""
    print("\n" + "=" * 60)
    print("🌐 測試 2: API 端點")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # 測試根路徑
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ GET / - 成功")
            endpoints = response.json().get("endpoints", {})
            print(f"   可用端點: {len(endpoints)} 個")
        else:
            print(f"❌ GET / - 失敗 (狀態碼: {response.status_code})")
    except Exception as e:
        print(f"❌ GET / - 錯誤: {e}")
        print("   請確認服務已啟動: python backend/main.py")
        return False
    
    # 測試健康檢查
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ GET /health - 成功")
        else:
            print(f"❌ GET /health - 失敗")
    except Exception as e:
        print(f"❌ GET /health - 錯誤: {e}")
    
    # 測試專案配置 API
    try:
        response = requests.get(f"{base_url}/api/project-config", timeout=5)
        if response.status_code == 200:
            print("✅ GET /api/project-config - 成功")
            data = response.json()
            if data.get("status") == "success":
                config = data.get("data", {})
                print(f"   - 視訊模糊控制參數: ✓")
                print(f"   - 距離映射設定: ✓")
                print(f"   - YOLO 設備設定: {config.get('yolo_device', {}).get('device', 'N/A')}")
        else:
            print(f"❌ GET /api/project-config - 失敗")
    except Exception as e:
        print(f"❌ GET /api/project-config - 錯誤: {e}")
    
    # 測試統計資訊 API
    try:
        response = requests.get(f"{base_url}/api/detection/stats", timeout=5)
        if response.status_code == 200:
            print("✅ GET /api/detection/stats - 成功")
        else:
            print(f"❌ GET /api/detection/stats - 失敗")
    except Exception as e:
        print(f"❌ GET /api/detection/stats - 錯誤: {e}")
    
    return True


def test_page_access():
    """測試頁面訪問"""
    print("\n" + "=" * 60)
    print("📄 測試 3: 頁面訪問")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    pages = {
        "/flur": "FlurPaint 展覽頁面",
        "/flur-admin": "FlurPaint 後台管理",
        "/admin": "監控後台",
        "/docs": "API 文件"
    }
    
    for path, name in pages.items():
        try:
            response = requests.get(f"{base_url}{path}", timeout=5, allow_redirects=True)
            if response.status_code == 200:
                print(f"✅ {path} - {name} (可訪問)")
            else:
                print(f"⚠️  {path} - {name} (狀態碼: {response.status_code})")
        except Exception as e:
            print(f"❌ {path} - {name} (錯誤: {e})")
    
    return True


def print_summary():
    """列印測試摘要"""
    print("\n" + "=" * 60)
    print("📊 測試摘要")
    print("=" * 60)
    print("\n✅ 系統已就緒!")
    print("\n可用服務:")
    print("  🎨 展覽頁面:   http://localhost:8000/flur")
    print("  🎛️  後台管理:   http://localhost:8000/flur-admin")
    print("  📊 監控後台:   http://localhost:8000/admin")
    print("  📖 API 文件:   http://localhost:8000/docs")
    print("\nWebSocket 端點:")
    print("  🔌 影像串流:   ws://localhost:8000/ws/flur")
    print("  🔌 完整偵測:   ws://localhost:8000/ws/detection")
    print("  🔌 簡化串流:   ws://localhost:8000/ws/live")
    print("\n快捷鍵 (展覽頁面):")
    print("  Ctrl+Shift+D: 切換除錯模式")
    print("  Ctrl+Shift+E: 切換展覽模式")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    print("\n🎨 FlurPaint 互動藝術裝置 - 系統測試\n")
    
    # 執行測試
    config_ok = test_config_loading()
    
    if config_ok:
        api_ok = test_api_endpoints()
        if api_ok:
            test_page_access()
            print_summary()
    else:
        print("\n⚠️  請先確認配置檔案是否正確")
    
    print("\n測試完成!\n")
