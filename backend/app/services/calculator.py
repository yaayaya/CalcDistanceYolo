#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
距離計算器 (從 camera_test_gui_v2.py 提取並優化)
"""

import numpy as np
from collections import deque
from typing import Dict, Optional


class DistanceCalculator:
    """
    距離計算器 - 使用相似三角形原理計算人體距離
    支援自適應高度判斷和多種平滑化演算法
    """
    
    def __init__(self, config: Dict):
        """
        初始化距離計算器
        
        Args:
            config: 距離配置字典,包含 focal_length, real_person_height 等參數
        """
        self.config = config
        self.distance_history: Dict[int, deque] = {}  # 各追蹤 ID 的距離歷史 (移動平均用)
        self.display_distances: Dict[int, float] = {}  # 各追蹤 ID 的顯示距離 (EMA 平滑用)
        
    def calculate_distance(
        self, 
        box_height: float, 
        box_width: float, 
        track_id: Optional[int] = None
    ) -> float:
        """
        計算距離
        
        Args:
            box_height: 邊界框高度 (像素)
            box_width: 邊界框寬度 (像素)
            track_id: 追蹤 ID (可選,用於平滑化)
            
        Returns:
            距離 (cm)
        """
        if box_height <= 0:
            return 0.0
            
        focal_length = self.config["focal_length"]
        person_height = self.config["real_person_height"]
        
        # === 自適應高度調整 (根據姿態) ===
        if self.config.get("use_adaptive_height", True):
            aspect_ratio = box_height / box_width if box_width > 0 else 2.5
            
            # 根據長寬比判斷姿態
            if aspect_ratio >= self.config.get("standing_ratio", 2.5):
                # 站立姿態
                height_factor = 1.0
            elif aspect_ratio < 1.5:
                # 坐姿
                height_factor = self.config.get("sitting_height_factor", 0.6)
            else:
                # 蹲姿
                height_factor = self.config.get("crouching_height_factor", 0.75)
                
            person_height *= height_factor
        
        # === 核心公式: 相似三角形原理 ===
        # distance = (real_height × focal_length) / image_height
        distance = (person_height * focal_length) / box_height
        
        # === 數據平滑化 (移動平均) ===
        if self.config.get("use_smoothing", True) and track_id is not None:
            distance = self._smooth_distance(track_id, distance)
        
        # === 顯示平滑化 (指數移動平均 EMA) ===
        if self.config.get("use_display_smoothing", True) and track_id is not None:
            distance = self._smooth_display(track_id, distance)
        
        return distance
    
    def _smooth_distance(self, track_id: int, distance: float) -> float:
        """
        數據平滑化 - 移動平均法 (Moving Average)
        
        Args:
            track_id: 追蹤 ID
            distance: 當前距離
            
        Returns:
            平滑後的距離
        """
        smoothing_window = self.config.get("smoothing_window", 5)
        
        if track_id not in self.distance_history:
            self.distance_history[track_id] = deque(maxlen=smoothing_window)
        
        self.distance_history[track_id].append(distance)
        return np.mean(self.distance_history[track_id])
    
    def _smooth_display(self, track_id: int, distance: float) -> float:
        """
        顯示平滑化 - 指數移動平均法 (Exponential Moving Average)
        用於消除畫面跳動,提供更流暢的視覺效果
        
        公式: new_value = α × current + (1-α) × old_value
        
        Args:
            track_id: 追蹤 ID
            distance: 當前距離
            
        Returns:
            平滑後的顯示距離
        """
        alpha = self.config.get("display_smooth_factor", 0.3)
        
        if track_id not in self.display_distances:
            self.display_distances[track_id] = distance
        else:
            self.display_distances[track_id] = (
                alpha * distance + (1 - alpha) * self.display_distances[track_id]
            )
        
        return self.display_distances[track_id]
    
    def calibrate_focal_length(self, box_height: float, known_distance: float) -> float:
        """
        校準焦距
        
        Args:
            box_height: 已知距離時的邊界框高度 (像素)
            known_distance: 實際距離 (cm)
            
        Returns:
            計算出的焦距
        """
        person_height = self.config["real_person_height"]
        self.config["focal_length"] = (box_height * known_distance) / person_height
        return self.config["focal_length"]
    
    def multi_point_calibration(self, measurements: list) -> tuple:
        """
        多點校準 - 使用多個測量點計算平均焦距
        
        Args:
            measurements: 測量點列表 [(box_height, distance), ...]
            
        Returns:
            (平均焦距, 標準差)
        """
        person_height = self.config["real_person_height"]
        focal_lengths = [(h * d) / person_height for h, d in measurements]
        
        avg_focal = np.mean(focal_lengths)
        std_dev = np.std(focal_lengths)
        
        self.config["focal_length"] = avg_focal
        return avg_focal, std_dev
    
    def clear_history(self, track_id: Optional[int] = None):
        """
        清除歷史資料
        
        Args:
            track_id: 指定追蹤 ID,若為 None 則清除所有
        """
        if track_id is None:
            self.distance_history.clear()
            self.display_distances.clear()
        else:
            self.distance_history.pop(track_id, None)
            self.display_distances.pop(track_id, None)
