#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YOLO 偵測服務 - 核心偵測引擎
"""

import asyncio
import cv2
import time
import base64
import numpy as np
from collections import deque
from typing import Optional, Dict, Any, AsyncGenerator
from ultralytics import YOLO

from .calculator import DistanceCalculator
from ..utils.config_loader import load_sensor_config, get_model_path, load_project_config


class YOLODetectorService:
    """
    YOLO11 偵測服務
    負責攝影機管理、YOLO 推論、距離計算
    """
    
    def __init__(self):
        """初始化偵測服務"""
        self.config = load_sensor_config()
        self.project_config = load_project_config()
        self.model: Optional[YOLO] = None
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        
        # 距離計算器
        self.distance_calculator = DistanceCalculator(self.config["distance"])
        
        # 統計資料
        self.fps = 0
        self.actual_fps = 0
        self.total_detections = 0
        self.closest_distance = 0.0
        self.frame_times = deque(maxlen=30)
        self.start_time: Optional[float] = None
        
        # 當前偵測結果快照 (供 REST API 使用)
        self.current_snapshot: Optional[Dict[str, Any]] = None
        
        # 最新影像幀 (供 Flur 串流使用)
        self.current_frame: Optional[np.ndarray] = None
        
    def load_model(self):
        """載入 YOLO 模型"""
        if self.model is not None:
            return
            
        try:
            model_path = get_model_path()
            self.model = YOLO(str(model_path))
            
            # 從 project_config 讀取設備設定
            device = self.project_config.get("yolo_device", {}).get("device", "cpu")
            print(f"✅ YOLO 模型已載入: {model_path} (設備: {device})")
        except Exception as e:
            raise RuntimeError(f"無法載入 YOLO 模型: {e}")
    
    def start_camera(self):
        """啟動攝影機"""
        if self.cap is not None and self.cap.isOpened():
            return
            
        try:
            source = self.config["camera"]["source"]
            self.cap = cv2.VideoCapture(source)
            
            if not self.cap.isOpened():
                raise RuntimeError(f"無法開啟攝影機: {source}")
            
            # 設定解析度
            width = self.config["camera"]["width"]
            height = self.config["camera"]["height"]
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            print(f"✅ 攝影機已啟動: {source} ({width}x{height})")
        except Exception as e:
            raise RuntimeError(f"無法啟動攝影機: {e}")
    
    def stop_camera(self):
        """停止攝影機"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            print("⏹ 攝影機已停止")
    
    def rotate_frame(self, frame, angle):
        """
        旋轉影像
        
        Args:
            frame: 輸入影像
            angle: 旋轉角度 (0, 90, 180, 270)
        
        Returns:
            旋轉後的影像
        """
        if angle == 0:
            return frame
        elif angle == 90:
            return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        elif angle == 180:
            return cv2.rotate(frame, cv2.ROTATE_180)
        elif angle == 270:
            return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        else:
            return frame
    
    async def start_detection(self):
        """啟動偵測"""
        if self.is_running:
            return
            
        self.load_model()
        self.start_camera()
        self.is_running = True
        self.start_time = time.time()
        print("▶ 偵測器已啟動")
    
    async def stop_detection(self):
        """停止偵測"""
        self.is_running = False
        self.stop_camera()
        self.start_time = None
        print("⏹ 偵測器已停止")
    
    async def detection_stream(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        偵測串流 - 異步生成器
        持續產生偵測結果直到 is_running 為 False
        
        Yields:
            偵測結果字典,包含 detections, fps, closest_distance, total_count, timestamp
        """
        if not self.is_running:
            await self.start_detection()
        
        frame_count = 0
        fps_start = time.time()
        fps_counter = 0
        last_frame_time = time.time()
        
        # FPS 限制參數
        use_fps_limit = self.config["performance"]["use_fps_limit"]
        target_fps = self.config["performance"]["target_fps"]
        frame_interval = 1.0 / target_fps if use_fps_limit else 0
        vid_stride = self.config["model"]["vid_stride"]
        
        loop = asyncio.get_event_loop()
        
        while self.is_running:
            try:
                loop_start = time.time()
                
                # === 讀取影像 (在執行緒池執行,避免阻塞) ===
                ret, frame = await loop.run_in_executor(None, self.cap.read)
                
                if not ret:
                    print("⚠ 無法讀取影像,嘗試重新連接...")
                    await asyncio.sleep(1)
                    continue
                
                # === 套用旋轉 ===
                rotation_angle = self.config["camera"].get("rotation", 0)
                if rotation_angle != 0:
                    frame = self.rotate_frame(frame, rotation_angle)
                
                # 儲存當前幀供 Flur 串流使用
                self.current_frame = frame.copy()
                
                frame_count += 1
                
                # === 跳幀處理 ===
                if frame_count % vid_stride != 0:
                    continue
                
                # === YOLO 推論 (在執行緒池執行) ===
                results = await loop.run_in_executor(
                    None,
                    self._run_yolo_inference,
                    frame
                )
                
                # === 處理偵測結果 ===
                detection_data = self._process_results(results)
                
                # === FPS 計算 ===
                fps_counter += 1
                if time.time() - fps_start >= 1.0:
                    self.fps = fps_counter
                    fps_counter = 0
                    fps_start = time.time()
                
                # === 實際 FPS (含處理時間) ===
                frame_time = time.time() - last_frame_time
                self.frame_times.append(frame_time)
                avg_frame_time = np.mean(self.frame_times)
                self.actual_fps = int(1.0 / avg_frame_time) if avg_frame_time > 0 else 0
                last_frame_time = time.time()
                
                # === 更新統計資料 ===
                detection_data["fps"] = self.fps
                detection_data["actual_fps"] = self.actual_fps
                detection_data["timestamp"] = time.time()
                
                # 更新快照
                self.current_snapshot = detection_data
                
                # === 產生結果 ===
                yield detection_data
                
                # === FPS 限制 ===
                if use_fps_limit:
                    elapsed_time = time.time() - loop_start
                    sleep_time = frame_interval - elapsed_time
                    if sleep_time > 0:
                        await asyncio.sleep(sleep_time)
                        
            except Exception as e:
                print(f"❌ 偵測迴圈錯誤: {e}")
                await asyncio.sleep(0.1)
    
    def _run_yolo_inference(self, frame):
        """
        執行 YOLO 推論 (同步方法,供 run_in_executor 使用)
        
        Args:
            frame: 輸入影像 (numpy array)
            
        Returns:
            YOLO Results 物件
        """
        # 從 project_config 讀取設備設定
        device = self.project_config.get("yolo_device", {}).get("device", self.config["model"]["device"])
        
        results = self.model.track(
            source=frame,
            classes=[0],  # 只偵測人類
            conf=self.config["model"]["conf"],
            iou=self.config["model"]["iou"],
            imgsz=self.config["model"]["imgsz"],
            device=device,
            tracker=self.config["model"]["tracker"],
            persist=True,  # 保持追蹤 ID
            show=False,
            verbose=False
        )
        return results
    
    def _process_results(self, results) -> Dict[str, Any]:
        """
        處理 YOLO 偵測結果
        
        Args:
            results: YOLO Results 物件
            
        Returns:
            處理後的偵測資料字典
        """
        detections = []
        distances = []
        
        if results[0].boxes is not None and len(results[0].boxes) > 0:
            for box in results[0].boxes:
                # 取得邊界框資料
                xyxy = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = xyxy
                box_height = y2 - y1
                box_width = x2 - x1
                
                # 取得追蹤 ID
                track_id = int(box.id[0]) if box.id is not None else None
                
                # 計算距離
                distance = self.distance_calculator.calculate_distance(
                    box_height, box_width, track_id
                )
                distances.append(distance)
                
                # 取得信心度
                confidence = float(box.conf[0])
                
                # 組裝偵測資料
                detections.append({
                    "track_id": track_id,
                    "distance": round(distance, 1),
                    "bbox": [float(x1), float(y1), float(x2), float(y2)],
                    "confidence": round(confidence, 3)
                })
        
        # 更新統計
        self.total_detections = len(detections)
        self.closest_distance = round(min(distances), 1) if distances else 0.0
        
        return {
            "detections": detections,
            "total_count": self.total_detections,
            "closest_distance": self.closest_distance,
            "fps": self.fps,
            "actual_fps": self.actual_fps
        }
    
    def get_current_snapshot(self) -> Optional[Dict[str, Any]]:
        """
        取得當前偵測結果快照 (供 REST API 使用)
        
        Returns:
            最新的偵測結果,若尚未開始偵測則返回 None
        """
        return self.current_snapshot
    
    def get_stats(self) -> Dict[str, Any]:
        """
        取得統計資訊
        
        Returns:
            統計資料字典
        """
        return {
            "total_count": self.total_detections,
            "closest_distance": self.closest_distance,
            "fps": self.fps,
            "actual_fps": self.actual_fps,
            "is_running": self.is_running,
            "uptime": int(time.time() - self.start_time) if self.start_time else 0
        }
    
    async def reload_config(self):
        """
        重新載入配置並重啟偵測器
        用於後台修改 sensor_config.json 後手動刷新
        """
        was_running = self.is_running
        
        if was_running:
            await self.stop_detection()
        
        # 重新載入配置
        self.config = load_sensor_config()
        self.project_config = load_project_config()
        self.distance_calculator = DistanceCalculator(self.config["distance"])
        
        if was_running:
            await self.start_detection()
        
        print("🔄 配置已重新載入")
    
    def calculate_target_resolution(self, distance: float) -> tuple:
        """
        根據距離計算目標解析度
        
        Args:
            distance: 偵測到的距離 (cm)
            
        Returns:
            (width, height) 元組
        """
        blur_config = self.project_config.get("blur_control", {})
        distance_config = self.project_config.get("distance_mapping", {})
        
        min_width = blur_config.get("min_resolution_width", 320)
        max_width = blur_config.get("max_resolution_width", 1920)
        min_distance = distance_config.get("min_distance", 50)
        max_distance = distance_config.get("max_distance", 500)
        
        # 如果沒有偵測到人 (distance = 0),使用最大解析度
        if distance == 0:
            width = max_width
        else:
            # 限制距離在範圍內
            clamped_dist = max(min_distance, min(max_distance, distance))
            
            # 線性映射 (距離越近,解析度越低)
            ratio = (clamped_dist - min_distance) / (max_distance - min_distance)
            width = int(min_width + ratio * (max_width - min_width))
        
        # 保持 16:9 比例
        height = int(width * 9 / 16)
        
        # 確保是偶數 (某些編碼器要求)
        width = width - (width % 2)
        height = height - (height % 2)
        
        return (width, height)
    
    def calculate_target_quality(self, distance: float) -> int:
        """
        根據距離計算 JPEG 品質
        距雩越近，品質越低；距雩越遠，品質越高
        
        Args:
            distance: 偵測到的距離 (cm)
            
        Returns:
            JPEG 品質 (1-100)
        """
        streaming_config = self.project_config.get("flur_streaming", {})
        distance_config = self.project_config.get("distance_mapping", {})
        
        min_quality = streaming_config.get("min_jpeg_quality", 30)
        max_quality = streaming_config.get("max_jpeg_quality", 85)
        min_distance = distance_config.get("min_distance", 50)
        max_distance = distance_config.get("max_distance", 500)
        
        # 如果沒有偵測到人 (distance = 0),使用最高品質
        if distance == 0:
            return max_quality
        
        # 限制距離在範圍內
        clamped_dist = max(min_distance, min(max_distance, distance))
        
        # 線性映射 (距離越近,品質越低)
        ratio = (clamped_dist - min_distance) / (max_distance - min_distance)
        quality = int(min_quality + ratio * (max_quality - min_quality))
        
        # 限制在 1-100 範圍
        return max(1, min(100, quality))
    
    def resize_frame(self, frame: np.ndarray, target_size: tuple) -> Optional[np.ndarray]:
        """
        調整影像尺寸
        
        Args:
            frame: 原始影像
            target_size: 目標尺寸 (width, height)
            
        Returns:
            調整後的影像，若失敗則返回 None
        """
        try:
            # 驗證輸入
            if frame is None or frame.size == 0:
                print("⚠ resize_frame: 影像為空")
                return None
            
            if not isinstance(target_size, tuple) or len(target_size) != 2:
                print(f"⚠ resize_frame: 無效的目標尺寸 {target_size}")
                return None
            
            width, height = target_size
            if width <= 0 or height <= 0 or width > 4096 or height > 4096:
                print(f"⚠ resize_frame: 尺寸超出範圍 {width}x{height}")
                return None
            
            # 執行縮放
            return cv2.resize(frame, target_size, interpolation=cv2.INTER_AREA)
            
        except Exception as e:
            print(f"❌ resize_frame 錯誤: {e}")
            return None
    
    def encode_frame_to_base64(self, frame: np.ndarray, quality: int = 70) -> Optional[str]:
        """
        將影像幀編碼為 Base64 字串
        
        Args:
            frame: OpenCV 影像 (numpy array)
            quality: JPEG 壓縮品質 (1-100)，預設降低到 70 以提升速度
            
        Returns:
            Base64 編碼的 JPEG 影像字串，若失敗則返回 None
        """
        try:
            if frame is None or frame.size == 0:
                print("⚠ encode_frame_to_base64: 影像為空")
                return None
            
            # 限制品質範圍
            quality = max(1, min(100, quality))
            
            # 優化編碼參數以提升速度
            encode_param = [
                int(cv2.IMWRITE_JPEG_QUALITY), quality,
                int(cv2.IMWRITE_JPEG_OPTIMIZE), 0,  # 關閉優化以加速
                int(cv2.IMWRITE_JPEG_PROGRESSIVE), 0  # 關閉漸進式以加速
            ]
            success, buffer = cv2.imencode('.jpg', frame, encode_param)
            
            if not success:
                print("⚠ encode_frame_to_base64: JPEG 編碼失敗")
                return None
            
            return base64.b64encode(buffer).decode('utf-8')
            
        except Exception as e:
            print(f"❌ encode_frame_to_base64 錯誤: {e}")
            return None
    
    def get_current_frame_base64(self, quality: int = 70, target_resolution: Optional[tuple] = None) -> Optional[str]:
        """
        取得當前影像幀的 Base64 編碼
        
        Args:
            quality: JPEG 壓縮品質 (1-100)
            target_resolution: 目標解析度 (width, height)，若為 None 則使用原始解析度
            
        Returns:
            Base64 編碼的影像,若無影像則返回 None
        """
        try:
            if self.current_frame is None:
                return None
            
            frame = self.current_frame
            
            # 如果指定了目標解析度，先縮放影像
            if target_resolution is not None:
                frame = self.resize_frame(frame, target_resolution)
                if frame is None:
                    return None
            
            return self.encode_frame_to_base64(frame, quality)
            
        except Exception as e:
            print(f"❌ get_current_frame_base64 錯誤: {e}")
            return None
    
    def get_frame_with_resolution(self, distance: float, quality: Optional[int] = None, enable_dynamic_quality: bool = False) -> Optional[Dict[str, Any]]:
        """
        根據距離取得動態解析度的影像幀
        
        Args:
            distance: 偵測距離 (cm)
            quality: JPEG 壓縮品質 (1-100)，若為 None 且 enable_dynamic_quality=True 則自動計算
            enable_dynamic_quality: 是否啟用動態品質
            
        Returns:
            包含影像和解析度資訊的字典，若無影像則返回 None
        """
        try:
            if self.current_frame is None:
                return None
            
            # 計算目標解析度
            target_resolution = self.calculate_target_resolution(distance)
            
            # 計算 JPEG 品質
            if enable_dynamic_quality and quality is None:
                target_quality = self.calculate_target_quality(distance)
            else:
                target_quality = quality if quality is not None else 70
            
            # 調整影像尺寸
            resized_frame = self.resize_frame(self.current_frame, target_resolution)
            
            if resized_frame is None:
                print("⚠ get_frame_with_resolution: 影像縮放失敗")
                return None
            
            # 編碼為 Base64
            frame_base64 = self.encode_frame_to_base64(resized_frame, target_quality)
            
            return {
                "image": frame_base64,
                "resolution": {
                    "width": target_resolution[0],
                    "height": target_resolution[1]
                },
                "quality": target_quality
            }
            
        except Exception as e:
            print(f"❌ get_frame_with_resolution 錯誤: {e}")
            return None
