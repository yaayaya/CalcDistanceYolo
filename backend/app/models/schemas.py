#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pydantic 資料模型定義
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime


class DetectionBox(BaseModel):
    """單一偵測框資料"""
    track_id: Optional[int] = Field(None, description="追蹤 ID")
    distance: float = Field(..., description="距離 (cm)")
    bbox: List[float] = Field(..., description="邊界框座標 [x1, y1, x2, y2]")
    confidence: float = Field(..., description="信心度 (0-1)")


class DetectionResult(BaseModel):
    """完整偵測結果"""
    timestamp: float = Field(..., description="時間戳記")
    detections: List[DetectionBox] = Field(default_factory=list, description="偵測到的物件列表")
    fps: int = Field(0, description="當前 FPS")
    closest_distance: float = Field(0, description="最近距離 (cm)")
    total_count: int = Field(0, description="偵測人數")


class DetectionStats(BaseModel):
    """偵測統計資訊"""
    total_count: int = Field(0, description="當前偵測人數")
    closest_distance: float = Field(0, description="最近距離 (cm)")
    fps: int = Field(0, description="當前 FPS")
    actual_fps: int = Field(0, description="實際 FPS")
    is_running: bool = Field(False, description="偵測器是否運行中")


class NetworkConfig(BaseModel):
    """網路配置"""
    websocket_host: str = Field("0.0.0.0", description="WebSocket 主機位址")
    websocket_port: int = Field(8000, description="WebSocket 埠號")
    broadcast_interval: int = Field(33, description="廣播間隔 (毫秒)")


class ApiResponse(BaseModel):
    """標準 API 回應格式"""
    status: str = Field("success", description="狀態: success/error")
    message: Optional[str] = Field(None, description="訊息")
    data: Optional[Any] = Field(None, description="回傳資料")
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp(), description="回應時間戳記")
