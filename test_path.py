#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試配置檔案路徑
"""

from pathlib import Path

# 方法1: 從 admin_api.py 的角度
admin_api_path = Path(__file__).resolve().parent / "backend" / "app" / "api" / "admin_api.py"
print(f"admin_api.py 路徑: {admin_api_path}")
print(f"存在: {admin_api_path.exists()}")

# 方法2: 計算 BASE_DIR (從 admin_api.py 往上四層)
if admin_api_path.exists():
    base_dir = admin_api_path.parent.parent.parent.parent
    print(f"\nBASE_DIR: {base_dir}")
    
    # 配置檔案路徑
    config_path = base_dir / "backend" / "configs" / "project_config.json"
    print(f"project_config.json 路徑: {config_path}")
    print(f"存在: {config_path.exists()}")
    
    # 影片目錄
    videos_dir = base_dir / "frontend" / "videos"
    print(f"\nvideos 目錄: {videos_dir}")
    print(f"存在: {videos_dir.exists()}")

# 方法3: 直接從當前目錄
print("\n=== 從當前目錄 ===")
current_config = Path("backend/configs/project_config.json")
print(f"相對路徑: {current_config}")
print(f"存在: {current_config.exists()}")
print(f"絕對路徑: {current_config.resolve()}")

# 方法4: 從執行目錄
import os
print(f"\n當前工作目錄: {os.getcwd()}")
