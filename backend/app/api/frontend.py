#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RESTful API 端點 (前端展覽作品用)
"""

from fastapi import APIRouter, HTTPException
from ..models.schemas import DetectionResult, DetectionStats, NetworkConfig, ApiResponse
from ..services.detector import YOLODetectorService
from ..utils.config_loader import (
    load_network_config, 
    save_network_config, 
    load_project_config,
    save_project_config
)
from typing import Dict, Any


# 建立路由器
router = APIRouter(prefix="/api", tags=["frontend"])

# 全域服務實例 (在 main.py 中初始化)
detector_service: YOLODetectorService = None


def init_frontend_services(detector: YOLODetectorService):
    """
    初始化 Frontend API 服務 (由 main.py 呼叫)
    
    Args:
        detector: 偵測服務實例
    """
    global detector_service
    detector_service = detector


@router.get("/distance/current", response_model=ApiResponse)
async def get_current_distance():
    """
    取得最新距離資料快照 (REST 輪詢方式)
    
    Returns:
        最新的偵測結果
    """
    snapshot = detector_service.get_current_snapshot()
    
    if snapshot is None:
        return ApiResponse(
            status="error",
            message="偵測器尚未啟動或無可用資料",
            data=None
        )
    
    return ApiResponse(
        status="success",
        message="成功取得當前距離資料",
        data=snapshot
    )


@router.get("/detection/stats", response_model=ApiResponse)
async def get_detection_stats():
    """
    取得當前統計資訊
    
    Returns:
        統計資料 (人數、距離、FPS、運行狀態)
    """
    stats = detector_service.get_stats()
    
    return ApiResponse(
        status="success",
        message="成功取得統計資訊",
        data=stats
    )


@router.get("/network-config", response_model=ApiResponse)
async def get_network_config():
    """
    取得網路配置
    
    Returns:
        network_config.json 的內容
    """
    try:
        config = load_network_config()
        return ApiResponse(
            status="success",
            message="成功取得網路配置",
            data=config
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"讀取網路配置失敗: {str(e)}")


@router.put("/network-config", response_model=ApiResponse)
async def update_network_config(config: Dict[str, Any]):
    """
    更新網路配置
    
    Args:
        config: 新的網路配置字典
        
    Returns:
        更新結果
    """
    try:
        success = save_network_config(config)
        
        if success:
            return ApiResponse(
                status="success",
                message="網路配置已更新,請手動刷新連線以套用變更",
                data=config
            )
        else:
            raise HTTPException(status_code=500, detail="儲存網路配置失敗")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新網路配置失敗: {str(e)}")


@router.post("/detector/refresh", response_model=ApiResponse)
async def refresh_detector():
    """
    重新載入配置並重啟偵測器
    用於在 GUI 工具修改 sensor_config.json 後手動刷新
    
    Returns:
        重啟結果
    """
    try:
        await detector_service.reload_config()
        
        return ApiResponse(
            status="success",
            message="偵測器配置已重新載入"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新載入配置失敗: {str(e)}")


@router.get("/health", response_model=ApiResponse)
async def health_check():
    """
    健康檢查端點
    
    Returns:
        服務狀態
    """
    is_running = detector_service.is_running if detector_service else False
    
    return ApiResponse(
        status="success",
        message="服務運行正常",
        data={
            "detector_running": is_running,
            "service": "YOLO11 Distance Detection API",
            "version": "1.0.0"
        }
    )


@router.get("/project-config", response_model=ApiResponse)
async def get_project_config():
    """
    取得專案配置 (包含視訊模糊控制、YOLO設備等)
    
    Returns:
        project_config.json 的內容
    """
    try:
        config = load_project_config()
        return ApiResponse(
            status="success",
            message="成功取得專案配置",
            data=config
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"讀取專案配置失敗: {str(e)}")


@router.put("/project-config", response_model=ApiResponse)
async def update_project_config(config: Dict[str, Any]):
    """
    更新專案配置
    
    Args:
        config: 新的專案配置字典
        
    Returns:
        更新結果
    """
    try:
        success = save_project_config(config)
        
        if success:
            # 重新載入偵測器配置以套用 YOLO 設備變更
            await detector_service.reload_config()
            
            return ApiResponse(
                status="success",
                message="專案配置已更新並重新載入",
                data=config
            )
        else:
            raise HTTPException(status_code=500, detail="儲存專案配置失敗")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新專案配置失敗: {str(e)}")


@router.post("/project-config/reset", response_model=ApiResponse)
async def reset_project_config():
    """
    重置專案配置為預設值
    
    Returns:
        重置後的配置
    """
    try:
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
        
        success = save_project_config(default_config)
        
        if success:
            await detector_service.reload_config()
            
            return ApiResponse(
                status="success",
                message="專案配置已重置為預設值",
                data=default_config
            )
        else:
            raise HTTPException(status_code=500, detail="重置專案配置失敗")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重置專案配置失敗: {str(e)}")


@router.get("/camera-selection", response_model=ApiResponse)
async def get_camera_selection():
    """
    取得前端攝影機選擇設定
    
    Returns:
        前端應該使用的攝影機編號及可用攝影機清單
    """
    try:
        from ..utils.config_loader import load_sensor_config
        sensor_config = load_sensor_config()
        
        camera_config = sensor_config.get("camera", {})
        camera_selection = camera_config.get("frontend_camera_selection", 0)
        available_cameras = camera_config.get("available_cameras", [0, 1])
        camera_descriptions = camera_config.get("camera_descriptions", {})
        
        return ApiResponse(
            status="success",
            message="成功取得攝影機設定",
            data={
                "selected_camera": camera_selection,
                "available_cameras": available_cameras,
                "descriptions": camera_descriptions
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"讀取攝影機設定失敗: {str(e)}")


@router.put("/camera-selection", response_model=ApiResponse)
async def update_camera_selection(camera_id: int):
    """
    更新前端攝影機選擇設定
    
    Args:
        camera_id: 要使用的攝影機編號
        
    Returns:
        更新結果
    """
    try:
        from ..utils.config_loader import load_sensor_config, save_sensor_config
        sensor_config = load_sensor_config()
        
        if "camera" not in sensor_config:
            sensor_config["camera"] = {}
        
        # 更新前端攝影機選擇
        sensor_config["camera"]["frontend_camera_selection"] = camera_id
        
        # 儲存配置
        success = save_sensor_config(sensor_config)
        
        if success:
            return ApiResponse(
                status="success",
                message=f"前端攝影機已設定為: {camera_id}",
                data={
                    "selected_camera": camera_id
                }
            )
        else:
            raise HTTPException(status_code=500, detail="儲存攝影機設定失敗")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新攝影機設定失敗: {str(e)}")


@router.get("/distance-recovery-config", response_model=ApiResponse)
async def get_distance_recovery_config():
    """
    取得距離恢復機制配置
    
    Returns:
        distance_recovery 的設定內容
    """
    try:
        config = load_project_config()
        recovery_config = config.get("distance_recovery", {})
        
        return ApiResponse(
            status="success",
            message="成功取得距離恢復機制配置",
            data=recovery_config
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"讀取距離恢復機制配置失敗: {str(e)}")


@router.put("/distance-recovery-config", response_model=ApiResponse)
async def update_distance_recovery_config(config: Dict[str, Any]):
    """
    更新距離恢復機制配置
    
    Args:
        config: 新的距離恢復機制配置
        
    Returns:
        更新結果
    """
    try:
        project_config = load_project_config()
        
        # 更新 distance_recovery 區塊
        if "distance_recovery" not in project_config:
            project_config["distance_recovery"] = {}
        
        project_config["distance_recovery"].update(config)
        
        # 儲存配置
        success = save_project_config(project_config)
        
        if success:
            return ApiResponse(
                status="success",
                message="距離恢復機制配置已更新",
                data=project_config["distance_recovery"]
            )
        else:
            raise HTTPException(status_code=500, detail="儲存距離恢復機制配置失敗")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新距離恢復機制配置失敗: {str(e)}")

