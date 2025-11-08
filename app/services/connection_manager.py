#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket 連線管理器
"""

import asyncio
from typing import List, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    """
    WebSocket 連線管理器
    負責管理所有 WebSocket 連線的生命週期
    """
    
    def __init__(self, detector_service):
        """
        初始化連線管理器
        
        Args:
            detector_service: YOLODetectorService 實例
        """
        self.active_connections: List[WebSocket] = []
        self.detector_service = detector_service
        self.detector_lock = asyncio.Lock()
        self.broadcast_task: asyncio.Task = None
        
    async def connect(self, websocket: WebSocket):
        """
        接受新的 WebSocket 連線
        
        Args:
            websocket: WebSocket 連線物件
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ WebSocket 連線已建立 (總連線數: {len(self.active_connections)})")
        
        # 若為第一個連線,啟動偵測器
        async with self.detector_lock:
            if len(self.active_connections) == 1 and not self.detector_service.is_running:
                await self.detector_service.start_detection()
                # 啟動廣播任務
                if self.broadcast_task is None or self.broadcast_task.done():
                    self.broadcast_task = asyncio.create_task(self._broadcast_loop())
    
    async def disconnect(self, websocket: WebSocket):
        """
        移除 WebSocket 連線
        
        Args:
            websocket: WebSocket 連線物件
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"❌ WebSocket 連線已斷開 (剩餘連線數: {len(self.active_connections)})")
        
        # 若無任何連線,停止偵測器
        async with self.detector_lock:
            if len(self.active_connections) == 0 and self.detector_service.is_running:
                await self.detector_service.stop_detection()
                # 取消廣播任務
                if self.broadcast_task and not self.broadcast_task.done():
                    self.broadcast_task.cancel()
    
    async def broadcast(self, data: Dict[str, Any]):
        """
        廣播資料給所有連線的客戶端
        
        Args:
            data: 要廣播的資料字典
        """
        disconnected_clients = []
        
        for connection in self.active_connections[:]:  # 複製列表避免迭代時修改
            try:
                await connection.send_json(data)
            except WebSocketDisconnect:
                disconnected_clients.append(connection)
            except Exception as e:
                print(f"⚠ 廣播錯誤: {e}")
                disconnected_clients.append(connection)
        
        # 清理斷開的連線
        for client in disconnected_clients:
            await self.disconnect(client)
    
    async def _broadcast_loop(self):
        """
        廣播迴圈 - 持續從偵測器獲取資料並廣播
        """
        try:
            async for detection_data in self.detector_service.detection_stream():
                if len(self.active_connections) > 0:
                    await self.broadcast(detection_data)
                else:
                    # 無連線時停止廣播
                    break
        except asyncio.CancelledError:
            print("🛑 廣播任務已取消")
        except Exception as e:
            print(f"❌ 廣播迴圈錯誤: {e}")
    
    def get_connection_count(self) -> int:
        """取得當前連線數"""
        return len(self.active_connections)
    
    async def disconnect_all(self):
        """斷開所有連線"""
        for connection in self.active_connections[:]:
            try:
                await connection.close()
            except Exception as e:
                print(f"⚠ 關閉連線錯誤: {e}")
        
        self.active_connections.clear()
        
        # 停止偵測器
        if self.detector_service.is_running:
            await self.detector_service.stop_detection()
