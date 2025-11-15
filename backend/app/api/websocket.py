#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket API 端點
"""

import asyncio
import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.connection_manager import ConnectionManager
from ..services.detector import YOLODetectorService
from ..utils.config_loader import load_project_config


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
    互動藝術裝置串流 (FlurPaint 展覽作品用) - 優化版
    
    只回傳距離與人數資訊，不傳送影像，大幅提升效能:
    {
        "type": "distance_data",
        "distance": float,
        "total_count": int,
        "timestamp": float
    }
    
    新增離開延遲與模擬恢復機制:
    - 當偵測人數 = 0 時，觸發離開延遲計時器
    - 延遲時間過後，開始模擬距離逐步恢復到最大距離
    - 讓前端的所有藝術效果能平滑過渡到最清晰狀態
    """
    await websocket.accept()
    
    # 載入配置
    project_config = load_project_config()
    recovery_config = project_config.get("distance_recovery", {})
    distance_config = project_config.get("distance_mapping", {})
    
    # 離開延遲與恢復設定
    enabled = recovery_config.get("enabled", True)
    deactivation_delay_ms = recovery_config.get("deactivation_delay_ms", 1000)
    recovery_duration_ms = recovery_config.get("recovery_duration_ms", 3000)
    recovery_target_distance = recovery_config.get("recovery_target_distance", 500)
    
    # 狀態變數
    last_detection_time = time.time()
    is_recovering = False
    recovery_start_time = 0
    recovery_start_distance = 0
    last_valid_distance = 0
    
    try:
        # 確保偵測器已啟動
        if not detector_service.is_running:
            await detector_service.start_detection()
        
        # 訂閱偵測串流
        async for detection_data in detector_service.detection_stream():
            current_time = time.time()
            
            # 取得原始偵測資料
            raw_distance = detection_data.get("closest_distance", 0)
            total_count = detection_data.get("total_count", 0)
            
            # 判斷是否有有效偵測 (人數 > 0 且距離 > 0)
            has_valid_detection = total_count > 0 and raw_distance > 0
            
            # 最終輸出的距離
            output_distance = raw_distance
            
            if has_valid_detection:
                # 有人偵測到，重置狀態
                last_detection_time = current_time
                last_valid_distance = raw_distance
                is_recovering = False
                output_distance = raw_distance
                
            else:
                # 沒有偵測到人
                if not enabled:
                    # 未啟用恢復機制，直接輸出 0
                    output_distance = 0
                else:
                    # 啟用恢復機制
                    time_since_last_detection = (current_time - last_detection_time) * 1000  # 轉換為 ms
                    
                    if time_since_last_detection < deactivation_delay_ms:
                        # 在延遲期間內，保持最後的有效距離
                        output_distance = last_valid_distance
                        
                    else:
                        # 延遲時間已過，開始恢復
                        if not is_recovering:
                            # 第一次進入恢復狀態，初始化
                            is_recovering = True
                            recovery_start_time = current_time
                            recovery_start_distance = last_valid_distance if last_valid_distance > 0 else distance_config.get("min_distance", 70)
                        
                        # 計算恢復進度 (0.0 到 1.0)
                        recovery_elapsed = (current_time - recovery_start_time) * 1000  # ms
                        recovery_progress = min(1.0, recovery_elapsed / recovery_duration_ms)
                        
                        # 套用 ease-out 緩動函數 (快速開始，慢慢結束)
                        eased_progress = 1 - pow(1 - recovery_progress, 2)
                        
                        # 線性插值從起始距離到目標距離
                        output_distance = recovery_start_distance + (recovery_target_distance - recovery_start_distance) * eased_progress
            
            # 組裝資料並發送
            flur_data = {
                "type": "distance_data",
                "distance": round(output_distance, 1),
                "total_count": total_count,
                "timestamp": current_time,
                "is_recovering": is_recovering  # 除錯用，讓前端知道是否在恢復狀態
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

