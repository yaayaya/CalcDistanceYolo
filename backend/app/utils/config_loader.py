#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置檔載入工具
"""

import json
import os
from pathlib import Path
from typing import Dict, Any


# 配置檔案路徑
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SENSOR_CONFIG_PATH = BASE_DIR / "configs" / "sensor_config.json"
NETWORK_CONFIG_PATH = BASE_DIR / "configs" / "network_config.json"


def load_sensor_config() -> Dict[str, Any]:
    """
    載入感測器配置 (sensor_config.json)
    此檔案由 GUI 工具調整,FastAPI 只讀取不修改
    """
    try:
        with open(SENSOR_CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        raise FileNotFoundError(f"找不到配置檔案: {SENSOR_CONFIG_PATH}")
    except json.JSONDecodeError as e:
        raise ValueError(f"配置檔案格式錯誤: {e}")


def load_network_config() -> Dict[str, Any]:
    """
    載入網路配置 (network_config.json)
    此檔案可透過後台 API 修改
    """
    try:
        with open(NETWORK_CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        # 使用預設值
        default_config = {
            "websocket": {
                "host": "0.0.0.0",
                "port": 8000,
                "broadcast_interval": 33  # 約 30 FPS
            }
        }
        # 自動建立預設配置檔案
        save_network_config(default_config)
        return default_config
    except json.JSONDecodeError as e:
        raise ValueError(f"網路配置檔案格式錯誤: {e}")


def save_network_config(config: Dict[str, Any]) -> bool:
    """
    儲存網路配置
    """
    try:
        # 確保 configs 目錄存在
        NETWORK_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        with open(NETWORK_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"儲存網路配置失敗: {e}")
        return False


def get_model_path() -> Path:
    """取得 YOLO 模型路徑"""
    sensor_config = load_sensor_config()
    model_filename = sensor_config["model"]["model_path"]
    
    # 優先在 models 目錄尋找 (專案根目錄下的 models/)
    model_path = BASE_DIR.parent / "models" / model_filename
    if model_path.exists():
        return model_path
    
    # 兼容: 專案根目錄 (repo root)
    root_path = BASE_DIR.parent / model_filename
    if root_path.exists():
        return root_path
    
    # 兼容舊路徑: backend 目錄下
    backend_path = BASE_DIR / model_filename
    if backend_path.exists():
        return backend_path
    
    # 兼容舊路徑:基本偵測資料夾
    tools_path = BASE_DIR.parent / "tools" / "基本偵測" / model_filename
    if tools_path.exists():
        return tools_path
    
    raise FileNotFoundError(f"找不到 YOLO 模型檔案: {model_filename}")
