#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
後台管理 API 端點
提供專案配置管理和影片管理功能
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse

from ..models.schemas import ApiResponse


# 建立路由器
router = APIRouter(prefix="/api/admin", tags=["admin"])

# 取得專案根目錄的絕對路徑
# 無論從哪裡啟動,都能找到正確的配置檔案
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
PROJECT_CONFIG_PATH = BASE_DIR / "backend" / "configs" / "project_config.json"
VIDEOS_DIR = BASE_DIR / "frontend" / "videos"

# 如果從 backend 目錄啟動,調整路徑
if not PROJECT_CONFIG_PATH.exists():
    # 可能從 backend/ 啟動,往上一層再找
    alt_base = Path(__file__).resolve().parent.parent.parent
    alt_config_path = alt_base / "configs" / "project_config.json"
    if alt_config_path.exists():
        BASE_DIR = alt_base.parent
        PROJECT_CONFIG_PATH = alt_config_path
        VIDEOS_DIR = BASE_DIR / "frontend" / "videos"

print(f"📂 BASE_DIR: {BASE_DIR}")
print(f"📄 CONFIG: {PROJECT_CONFIG_PATH}")
print(f"🎬 VIDEOS: {VIDEOS_DIR}")

# 確保目錄存在
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

# 確保配置檔案存在
if not PROJECT_CONFIG_PATH.exists():
    print(f"⚠️ 配置檔案不存在,建立預設配置: {PROJECT_CONFIG_PATH}")
    default_config = {
        "video": {
            "currentVideo": "",
            "baseSpeed": 1.0,
            "maxSpeed": 10.0,
            "minSpeed": 0.25,
            "loop": True,
            "muted": False,
            "autoplay": True,
            "transitionTime": 500,
            "reverseMode": False
        },
        "distance": {
            "minDistance": 50,
            "maxDistance": 500,
            "closestPersonMode": True,
            "distanceThreshold": 10,
            "smoothingFactor": 0.3,
            "activationDelay": 300,
            "deactivationDelay": 1000,
            "noFaceTimeout": 3000
        },
        "display": {
            "debugMode": False,
            "showSpeed": True,
            "showDistance": True,
            "showFaceCount": True,
            "showFPS": True,
            "showCameraPreview": False,
            "cursorHideDelay": 2000,
            "exhibitionMode": False
        },
        "calibration": {
            "defaultPresets": [
                {"name": "正常模式", "baseSpeed": 1.0, "maxSpeed": 10.0, "minDistance": 50, "maxDistance": 500},
                {"name": "快速模式", "baseSpeed": 2.0, "maxSpeed": 15.0, "minDistance": 50, "maxDistance": 400},
                {"name": "慢速模式", "baseSpeed": 0.5, "maxSpeed": 5.0, "minDistance": 100, "maxDistance": 600},
                {"name": "展示模式", "baseSpeed": 1.0, "maxSpeed": 8.0, "minDistance": 80, "maxDistance": 450}
            ]
        }
    }
    PROJECT_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PROJECT_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, ensure_ascii=False, indent=2)

# 支援的影片格式
SUPPORTED_FORMATS = {".mp4", ".webm", ".ogg"}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB


def load_project_config() -> Dict[str, Any]:
    """載入專案配置"""
    try:
        if not PROJECT_CONFIG_PATH.exists():
            raise HTTPException(
                status_code=404, 
                detail=f"專案配置檔案不存在: {PROJECT_CONFIG_PATH}"
            )
        
        with open(PROJECT_CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
            print(f"✅ 成功載入配置: {PROJECT_CONFIG_PATH}")
            return config
            
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"配置檔案格式錯誤: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"載入配置失敗: {str(e)}"
        )


def save_project_config(config: Dict[str, Any]) -> bool:
    """儲存專案配置"""
    try:
        PROJECT_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(PROJECT_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"✅ 成功儲存配置: {PROJECT_CONFIG_PATH}")
        return True
    except Exception as e:
        print(f"❌ 儲存配置失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"儲存配置失敗: {str(e)}")


@router.get("/config", response_model=ApiResponse)
async def get_config():
    """
    取得完整專案配置
    
    Returns:
        專案配置資料
    """
    try:
        config = load_project_config()
        return ApiResponse(
            status="success",
            message="成功取得專案配置",
            data=config
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config", response_model=ApiResponse)
async def update_config(config_update: Dict[str, Any]):
    """
    更新專案配置 (部分更新)
    
    Args:
        config_update: 要更新的配置區塊
        
    Returns:
        更新後的完整配置
    """
    try:
        current_config = load_project_config()
        
        # 遞迴更新配置
        def deep_update(base: dict, update: dict):
            for key, value in update.items():
                if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                    deep_update(base[key], value)
                else:
                    base[key] = value
        
        deep_update(current_config, config_update)
        
        # 儲存更新後的配置
        save_project_config(current_config)
        
        return ApiResponse(
            status="success",
            message="配置已成功更新",
            data=current_config
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失敗: {str(e)}")


@router.post("/config/reset", response_model=ApiResponse)
async def reset_config():
    """
    重置配置為預設值
    
    Returns:
        重置後的配置
    """
    default_config = {
        "video": {
            "currentVideo": "",
            "baseSpeed": 1.0,
            "maxSpeed": 10.0,
            "minSpeed": 0.25,
            "loop": True,
            "muted": False,
            "autoplay": True,
            "transitionTime": 500,
            "reverseMode": False
        },
        "distance": {
            "minDistance": 50,
            "maxDistance": 500,
            "closestPersonMode": True,
            "distanceThreshold": 10,
            "smoothingFactor": 0.3,
            "activationDelay": 300,
            "deactivationDelay": 1000,
            "noFaceTimeout": 3000
        },
        "display": {
            "debugMode": False,
            "showSpeed": True,
            "showDistance": True,
            "showFaceCount": True,
            "showFPS": True,
            "showCameraPreview": False,
            "cursorHideDelay": 2000,
            "exhibitionMode": False
        },
        "calibration": {
            "defaultPresets": [
                {"name": "正常模式", "baseSpeed": 1.0, "maxSpeed": 10.0, "minDistance": 50, "maxDistance": 500},
                {"name": "快速模式", "baseSpeed": 2.0, "maxSpeed": 15.0, "minDistance": 50, "maxDistance": 400},
                {"name": "慢速模式", "baseSpeed": 0.5, "maxSpeed": 5.0, "minDistance": 100, "maxDistance": 600},
                {"name": "展示模式", "baseSpeed": 1.0, "maxSpeed": 8.0, "minDistance": 80, "maxDistance": 450}
            ]
        }
    }
    
    try:
        save_project_config(default_config)
        return ApiResponse(
            status="success",
            message="配置已重置為預設值",
            data=default_config
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重置配置失敗: {str(e)}")


@router.get("/videos", response_model=ApiResponse)
async def list_videos():
    """
    取得影片列表
    
    Returns:
        影片檔案資訊列表
    """
    try:
        videos = []
        
        if VIDEOS_DIR.exists():
            for file in VIDEOS_DIR.iterdir():
                if file.is_file() and file.suffix.lower() in SUPPORTED_FORMATS:
                    videos.append({
                        "filename": file.name,
                        "size": file.stat().st_size,
                        "path": f"videos/{file.name}"
                    })
        
        return ApiResponse(
            status="success",
            message=f"找到 {len(videos)} 個影片",
            data=videos
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"讀取影片列表失敗: {str(e)}")


@router.post("/videos/upload", response_model=ApiResponse)
async def upload_video(file: UploadFile = File(...)):
    """
    上傳影片
    
    Args:
        file: 上傳的影片檔案
        
    Returns:
        上傳結果
    """
    try:
        # 檢查檔案格式
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in SUPPORTED_FORMATS:
            raise HTTPException(
                status_code=400, 
                detail=f"不支援的檔案格式。支援格式: {', '.join(SUPPORTED_FORMATS)}"
            )
        
        # 檢查檔案大小
        file.file.seek(0, 2)  # 移到檔案結尾
        file_size = file.file.tell()
        file.file.seek(0)  # 回到開頭
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"檔案大小超過限制 ({MAX_FILE_SIZE / (1024*1024):.0f}MB)"
            )
        
        # 確保影片目錄存在
        VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
        
        # 儲存檔案
        file_path = VIDEOS_DIR / file.filename
        
        print(f"📤 上傳影片: {file.filename} ({file_size / (1024*1024):.2f}MB)")
        print(f"   儲存路徑: {file_path}")
        
        with open(file_path, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"✅ 上傳成功: {file.filename}")
        
        return ApiResponse(
            status="success",
            message=f"影片 {file.filename} 上傳成功",
            data={
                "filename": file.filename,
                "size": file_size,
                "path": f"videos/{file.filename}"
            }
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上傳失敗: {str(e)}")


@router.delete("/videos/{filename}", response_model=ApiResponse)
async def delete_video(filename: str):
    """
    刪除影片
    
    Args:
        filename: 影片檔名
        
    Returns:
        刪除結果
    """
    try:
        file_path = VIDEOS_DIR / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="影片不存在")
        
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail="不是有效的檔案")
        
        # 檢查是否為當前使用的影片
        config = load_project_config()
        if config.get("video", {}).get("currentVideo") == filename:
            # 清除 currentVideo
            config["video"]["currentVideo"] = ""
            save_project_config(config)
        
        # 刪除檔案
        file_path.unlink()
        
        return ApiResponse(
            status="success",
            message=f"影片 {filename} 已刪除"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刪除失敗: {str(e)}")


@router.put("/videos/current/{filename}", response_model=ApiResponse)
async def set_current_video(filename: str):
    """
    設定當前播放影片
    
    Args:
        filename: 影片檔名
        
    Returns:
        更新結果
    """
    try:
        file_path = VIDEOS_DIR / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="影片不存在")
        
        # 更新配置
        config = load_project_config()
        config["video"]["currentVideo"] = filename
        save_project_config(config)
        
        return ApiResponse(
            status="success",
            message=f"當前影片已設定為: {filename}",
            data={"currentVideo": filename}
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"設定失敗: {str(e)}")


@router.get("/videos/{filename}/info", response_model=ApiResponse)
async def get_video_info(filename: str):
    """
    取得影片詳細資訊
    
    Args:
        filename: 影片檔名
        
    Returns:
        影片資訊
    """
    try:
        file_path = VIDEOS_DIR / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="影片不存在")
        
        stat = file_path.stat()
        
        return ApiResponse(
            status="success",
            message="成功取得影片資訊",
            data={
                "filename": filename,
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "path": f"videos/{filename}"
            }
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得影片資訊失敗: {str(e)}")
