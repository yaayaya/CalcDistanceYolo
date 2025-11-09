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
PROJECT_CONFIG_PATH = BASE_DIR / "configs" / "project_config.json"


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
    
    # 搜尋路徑列表 (依優先順序)
    search_paths = [
        BASE_DIR.parent / model_filename,                    # 專案根目錄
        BASE_DIR.parent / "models" / model_filename,         # models 資料夾
        BASE_DIR / model_filename,                           # backend 資料夾
        BASE_DIR.parent / "tools" / "基本偵測" / model_filename,  # 工具資料夾
    ]
    
    # 依序尋找模型檔案
    for model_path in search_paths:
        if model_path.exists():
            return model_path
    
    # 找不到模型檔案,列出所有嘗試過的路徑
    searched_paths = "\n  - ".join(str(p) for p in search_paths)
    raise FileNotFoundError(
        f"找不到 YOLO 模型檔案: {model_filename}\n"
        f"已搜尋以下路徑:\n  - {searched_paths}"
    )


def load_project_config() -> Dict[str, Any]:
    """
    載入專案配置 (project_config.json)
    包含視訊模糊控制參數、YOLO設備選項等
    """
    try:
        with open(PROJECT_CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        # 使用預設值
        default_config = {
            "blur_control": {
                "min_resolution_width": 320,
                "max_resolution_width": 1920,
                "acceleration_time": 500,
                "deceleration_time": 1000,
                "movement_threshold": 10,
                "activation_delay": 200,
                "deactivation_delay": 500,
                "sample_rate": 30
            },
            "distance_mapping": {
                "min_distance": 50,
                "max_distance": 500,
                "easing_function": "linear"
            },
            "display": {
                "debug_mode": False,
                "exhibition_mode": True,
                "show_fps": False,
                "show_distance": False
            },
            "yolo_device": {
                "device": "cpu",
                "available_devices": ["cpu", "cuda", "mps"],
                "device_description": {
                    "cpu": "使用 CPU 進行推論 (相容性最佳)",
                    "cuda": "使用 NVIDIA GPU (需要 CUDA 支援)",
                    "mps": "使用 Apple Silicon GPU (M1/M2/M3 晶片)"
                }
            }
        }
        # 自動建立預設配置檔案
        save_project_config(default_config)
        return default_config
    except json.JSONDecodeError as e:
        raise ValueError(f"專案配置檔案格式錯誤: {e}")


def save_project_config(config: Dict[str, Any]) -> bool:
    """
    儲存專案配置
    """
    try:
        # 確保 configs 目錄存在
        PROJECT_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        with open(PROJECT_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"儲存專案配置失敗: {e}")
        return False


def save_sensor_config(config: Dict[str, Any]) -> bool:
    """
    儲存感測器配置
    """
    try:
        # 確保 configs 目錄存在
        SENSOR_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        with open(SENSOR_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"儲存感測器配置失敗: {e}")
        return False


