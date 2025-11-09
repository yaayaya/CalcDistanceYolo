#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket API 端點
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.connection_manager import ConnectionManager
from ..services.detector import YOLODetectorService


# 建立路由器
router = APIRouter()

# 全域服務實例 (在 main.py 中初始化)
detector_service: YOLODetectorService = None
connection_manager: ConnectionManager = None


def init_websocket_services(detector: YOLODetectorService, manager: ConnectionManager):
    """
    初始化 WebSocket 服務 (由 main.py 呼叫)
    
    Args:
        detector: 偵測服務實例
        manager: 連線管理器實例
    """
    global detector_service, connection_manager
    detector_service = detector
    connection_manager = manager


@router.websocket("/ws/detection")
async def websocket_detection(websocket: WebSocket):
    """
    完整偵測資料串流 (後台監控用)
    
    回傳格式:
    {
        "detections": [
            {
                "track_id": int,
                "distance": float,
                "bbox": [x1, y1, x2, y2],
                "confidence": float
            }
        ],
        "fps": int,
        "actual_fps": int,
        "closest_distance": float,
        "total_count": int,
        "timestamp": float
    }
    """
    await connection_manager.connect(websocket)
    
    try:
        # 保持連線直到客戶端斷開
        while True:
            # 等待客戶端訊息 (用於心跳檢測)
            try:
                data = await websocket.receive_text()
                
                # 處理特殊指令
                if data == "ping":
                    await websocket.send_text("pong")
                    
            except WebSocketDisconnect:
                break
                
    except Exception as e:
        print(f"❌ WebSocket 錯誤: {e}")
    finally:
        await connection_manager.disconnect(websocket)


@router.websocket("/ws/live")
async def websocket_live(websocket: WebSocket):
    """
    簡化版即時串流 (前端展覽作品用)
    
    只回傳距離和人數資訊,減少資料量:
    {
        "closest_distance": float,
        "total_count": int,
        "timestamp": float
    }
    """
    await websocket.accept()
    
    try:
        # 訂閱偵測串流
        async for detection_data in detector_service.detection_stream():
            # 簡化資料
            simplified_data = {
                "closest_distance": detection_data.get("closest_distance", 0),
                "total_count": detection_data.get("total_count", 0),
                "timestamp": detection_data.get("timestamp", 0)
            }
            
            try:
                await websocket.send_json(simplified_data)
            except WebSocketDisconnect:
                break
                
    except Exception as e:
        print(f"❌ WebSocket Live 錯誤: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass


@router.websocket("/ws/flur")
async def websocket_flur(websocket: WebSocket):
    """
    互動藝術裝置串流 (FlurPaint 展覽作品用)
    
    回傳影像幀與距離資料 - 影像解析度和 JPEG 品質根據距離動態調整:
    {
        "type": "frame_data",
        "image": "base64_encoded_jpeg",
        "distance": float,
        "total_count": int,
        "timestamp": float,
        "resolution": {
            "width": int,
            "height": int
        },
        "quality": int
    }
    """
    await websocket.accept()
    
    try:
        # 確保偵測器已啟動
        if not detector_service.is_running:
            await detector_service.start_detection()
        
        # 讀取串流配置
        streaming_config = detector_service.project_config.get("flur_streaming", {})
        jpeg_quality = streaming_config.get("jpeg_quality", 70)
        enable_dynamic = streaming_config.get("enable_dynamic_resolution", True)
        enable_dynamic_quality = streaming_config.get("enable_dynamic_quality", False)
        
        # 訂閱偵測串流
        async for detection_data in detector_service.detection_stream():
            # 取得距離
            distance = detection_data.get("closest_distance", 0)
            
            if enable_dynamic:
                # 根據距離取得動態解析度的影像幀
                frame_data = detector_service.get_frame_with_resolution(
                    distance=distance,
                    quality=jpeg_quality if not enable_dynamic_quality else None,
                    enable_dynamic_quality=enable_dynamic_quality
                )
            else:
                # 使用原始解析度
                frame_base64 = detector_service.get_current_frame_base64(quality=jpeg_quality)
                frame_data = {
                    "image": frame_base64,
                    "resolution": {"width": 1920, "height": 1080},
                    "quality": jpeg_quality
                } if frame_base64 else None
            
            if frame_data is None:
                continue
            
            # 組裝資料
            flur_data = {
                "type": "frame_data",
                "image": frame_data["image"],
                "distance": distance,
                "total_count": detection_data.get("total_count", 0),
                "timestamp": detection_data.get("timestamp", 0),
                "resolution": frame_data["resolution"],
                "quality": frame_data.get("quality", jpeg_quality)
            }
            
            try:
                await websocket.send_json(flur_data)
            except WebSocketDisconnect:
                break
                
    except Exception as e:
        print(f"❌ WebSocket Flur 錯誤: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass

