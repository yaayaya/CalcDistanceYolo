#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YOLO11n 距離偵測系統 v3.1 - 優化 GUI 版本
新增功能:
- 自動帶入校準參數
- FPS 限制選項
- 平滑距離顯示
- Flask 後端 API 模組
"""

# 解決 OpenMP 函式庫衝突問題
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import cv2
import numpy as np
import time
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import threading
from ultralytics import YOLO
from collections import deque


class ConfigManager:
    """配置檔管理器"""
    
    @staticmethod
    def get_config_path(config_path=None):
        """取得配置檔絕對路徑"""
        if config_path and os.path.isabs(config_path):
            return config_path
        
        # 從當前檔案位置計算專案根目錄
        current_file = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
        return os.path.join(project_root, "backend", "configs", "sensor_config.json")
    
    @staticmethod
    def load_config(config_path=None):
        """載入 JSON 配置檔"""
        config_path = ConfigManager.get_config_path(config_path)
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"✓ 成功載入配置檔: {config_path}")
            return config
        except FileNotFoundError:
            print(f"⚠️ 找不到配置檔 {config_path}, 使用預設值")
            return ConfigManager.default_config()
        except json.JSONDecodeError as e:
            print(f"❌ 配置檔格式錯誤: {e}")
            return ConfigManager.default_config()
    
    @staticmethod
    def save_config(config, config_path=None):
        """儲存配置到 JSON 檔"""
        config_path = ConfigManager.get_config_path(config_path)
        try:
            # 確保目錄存在
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"✓ 配置已儲存至: {config_path}")
            return True
        except Exception as e:
            print(f"❌ 儲存配置失敗: {e}")
            return False
    
    @staticmethod
    def default_config():
        """預設配置"""
        return {
            "model": {
                "model_path": "yolo11n.pt",
                "imgsz": 416,
                "conf": 0.5,
                "iou": 0.5,
                "device": "cpu",
                "vid_stride": 3,
                "tracker": "botsort.yaml"
            },
            "distance": {
                "focal_length": 600,
                "real_person_height": 170,
                "use_adaptive_height": True,
                "use_smoothing": True,
                "use_display_smoothing": True,
                "smoothing_window": 5,
                "display_smooth_factor": 0.3,
                "standing_ratio": 2.5,
                "sitting_height_factor": 0.6,
                "crouching_height_factor": 0.75
            },
            "camera": {
                "source": 0,
                "width": 640,
                "height": 480
            },
            "performance": {
                "use_fps_limit": False,
                "target_fps": 30
            },
            "runtime": {
                "max_runtime_hours": 8,
                "health_check_interval": 300,
                "auto_reconnect": True,
                "max_consecutive_errors": 50
            },
            "output": {
                "show": True,
                "save_video": False,
                "output_path": "output.mp4",
                "save_txt": False
            }
        }


class DistanceCalculator:
    """距離計算器 (可供 Flask 後端使用)"""
    
    def __init__(self, config):
        self.config = config
        self.distance_history = {}
        self.display_distances = {}
        
    def calculate_distance(self, box_height, box_width, track_id=None):
        """計算距離"""
        focal_length = self.config["distance"]["focal_length"]
        person_height = self.config["distance"]["real_person_height"]
        
        # 自適應高度
        if self.config["distance"]["use_adaptive_height"]:
            aspect_ratio = box_height / box_width if box_width > 0 else 2.5
            if aspect_ratio >= self.config["distance"]["standing_ratio"]:
                height_factor = 1.0
            elif aspect_ratio < 1.5:
                height_factor = self.config["distance"]["sitting_height_factor"]
            else:
                height_factor = self.config["distance"]["crouching_height_factor"]
            person_height *= height_factor
        
        # 計算距離
        distance = (person_height * focal_length) / box_height if box_height > 0 else 0
        
        # 數據平滑化
        if self.config["distance"].get("use_smoothing", True) and track_id is not None:
            distance = self._smooth_distance(track_id, distance)
        
        # 顯示平滑化
        if self.config["distance"].get("use_display_smoothing", True) and track_id is not None:
            distance = self._smooth_display(track_id, distance)
        
        return distance
    
    def _smooth_distance(self, track_id, distance):
        """數據平滑化 (移動平均)"""
        if track_id not in self.distance_history:
            self.distance_history[track_id] = deque(maxlen=self.config["distance"].get("smoothing_window", 5))
        
        self.distance_history[track_id].append(distance)
        return np.mean(self.distance_history[track_id])
    
    def _smooth_display(self, track_id, distance):
        """顯示平滑化 (指數移動平均)"""
        alpha = self.config["distance"].get("display_smooth_factor", 0.3)
        
        if track_id not in self.display_distances:
            self.display_distances[track_id] = distance
        else:
            self.display_distances[track_id] = (
                alpha * distance + (1 - alpha) * self.display_distances[track_id]
            )
        
        return self.display_distances[track_id]
    
    def calibrate_focal_length(self, box_height, known_distance):
        """校準焦距"""
        person_height = self.config["distance"]["real_person_height"]
        self.config["distance"]["focal_length"] = (box_height * known_distance) / person_height
        return self.config["distance"]["focal_length"]
    
    def multi_point_calibration(self, measurements):
        """多點校準"""
        person_height = self.config["distance"]["real_person_height"]
        focal_lengths = [(h * d) / person_height for h, d in measurements]
        avg_focal = np.mean(focal_lengths)
        std_dev = np.std(focal_lengths)
        self.config["distance"]["focal_length"] = avg_focal
        return avg_focal, std_dev


class YOLO11DistanceDetectorGUI:
    """YOLO11n 距離偵測器 - GUI版本"""
    
    def __init__(self, root, config_path=None):
        self.root = root
        self.root.title("YOLO11n 距離偵測系統 v3.1")
        self.root.geometry("1400x900")
        
        # 載入配置
        self.config_path = ConfigManager.get_config_path(config_path)
        self.config = ConfigManager.load_config(config_path)
        
        # 距離計算器
        self.distance_calculator = DistanceCalculator(self.config)
        
        # 初始化變數
        self.model = None
        self.detector_running = False
        self.cap = None
        self.detection_thread = None
        self.current_frame = None
        self.current_results = None  # 儲存當前偵測結果
        self.calibration_measurements = []
        
        # 統計資訊
        self.fps = 0
        self.actual_fps = 0
        self.total_detections = 0
        self.closest_distance = 0
        self.start_time = None
        self.frame_times = deque(maxlen=30)
        
        # 建立 UI
        self.setup_ui()
        
        # 載入模型
        self.load_model()
    
    def setup_ui(self):
        """建立使用者介面"""
        # ===== 左側面板:攝影機預覽 =====
        left_frame = ttk.Frame(self.root, padding="10")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # 標題
        title_label = ttk.Label(left_frame, text="📹 攝影機預覽", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=5)
        
        # 畫布
        self.canvas = tk.Canvas(left_frame, width=800, height=600, bg="black")
        self.canvas.pack(pady=5)
        self.canvas.bind("<Button-1>", self.on_canvas_click)  # 點擊取樣
        
        # 狀態列
        status_frame = ttk.LabelFrame(left_frame, text="即時狀態", padding="10")
        status_frame.pack(fill=tk.X, pady=5)
        
        self.status_text = tk.Text(status_frame, height=4, width=90, 
                                   font=("Consolas", 10))
        self.status_text.pack()
        
        # ===== 右側面板:控制與設定 =====
        right_frame = ttk.Frame(self.root, padding="10")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # 使用 Notebook 分頁
        notebook = ttk.Notebook(right_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 分頁1: 攝影機控制
        camera_tab = ttk.Frame(notebook, padding="10")
        notebook.add(camera_tab, text="攝影機控制")
        self.setup_camera_tab(camera_tab)
        
        # 分頁2: 智慧校準
        calibration_tab = ttk.Frame(notebook, padding="10")
        notebook.add(calibration_tab, text="智慧校準")
        self.setup_calibration_tab(calibration_tab)
        
        # 分頁3: 參數設定
        settings_tab = ttk.Frame(notebook, padding="10")
        notebook.add(settings_tab, text="參數設定")
        self.setup_settings_tab(settings_tab)
        
        # 分頁4: 統計資訊
        stats_tab = ttk.Frame(notebook, padding="10")
        notebook.add(stats_tab, text="統計資訊")
        self.setup_stats_tab(stats_tab)
        
        # 設定 grid 權重
        self.root.columnconfigure(0, weight=3)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)
    
    def setup_camera_tab(self, parent):
        """設定攝影機控制分頁"""
        # 攝影機來源
        source_frame = ttk.LabelFrame(parent, text="攝影機來源", padding="10")
        source_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(source_frame, text="來源:").grid(row=0, column=0, sticky=tk.W)
        self.source_var = tk.StringVar(value=str(self.config["camera"]["source"]))
        ttk.Entry(source_frame, textvariable=self.source_var, width=20).grid(
            row=0, column=1, padx=5)
        ttk.Label(source_frame, text="(0=攝影機, 或檔案路徑)").grid(
            row=0, column=2, sticky=tk.W)
        
        # 解析度
        ttk.Label(source_frame, text="解析度:").grid(row=1, column=0, sticky=tk.W, pady=5)
        res_frame = ttk.Frame(source_frame)
        res_frame.grid(row=1, column=1, columnspan=2)
        
        self.width_var = tk.IntVar(value=self.config["camera"]["width"])
        self.height_var = tk.IntVar(value=self.config["camera"]["height"])
        
        ttk.Entry(res_frame, textvariable=self.width_var, width=8).pack(side=tk.LEFT)
        ttk.Label(res_frame, text=" x ").pack(side=tk.LEFT)
        ttk.Entry(res_frame, textvariable=self.height_var, width=8).pack(side=tk.LEFT)
        
        # 儲存攝影機設定按鈕
        ttk.Button(source_frame, text="💾 儲存攝影機設定", 
                  command=self.save_camera_settings).grid(
            row=2, column=0, columnspan=3, pady=10)
        
        # 效能設定
        perf_frame = ttk.LabelFrame(parent, text="效能設定", padding="10")
        perf_frame.pack(fill=tk.X, pady=5)
        
        self.use_fps_limit_var = tk.BooleanVar(
            value=self.config.get("performance", {}).get("use_fps_limit", False))
        ttk.Checkbutton(perf_frame, text="啟用 FPS 限制", 
                       variable=self.use_fps_limit_var,
                       command=self.toggle_fps_limit).grid(
            row=0, column=0, columnspan=2, sticky=tk.W)
        
        ttk.Label(perf_frame, text="目標 FPS:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.target_fps_var = tk.IntVar(
            value=self.config.get("performance", {}).get("target_fps", 30))
        fps_spinbox = ttk.Spinbox(perf_frame, from_=1, to=60, 
                                  textvariable=self.target_fps_var, width=10)
        fps_spinbox.grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # 實際 FPS 顯示
        ttk.Label(perf_frame, text="實際 FPS:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.actual_fps_label = ttk.Label(perf_frame, text="0", 
                                         font=("Arial", 10, "bold"))
        self.actual_fps_label.grid(row=2, column=1, sticky=tk.W, padx=5)
        
        # 儲存效能設定按鈕
        ttk.Button(perf_frame, text="💾 儲存效能設定", 
                  command=self.save_performance_settings).grid(
            row=3, column=0, columnspan=2, pady=10, sticky=tk.W)
        
        # 控制按鈕
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=20)
        
        self.start_btn = ttk.Button(btn_frame, text="▶ 啟動偵測", 
                                    command=self.start_detection, width=20)
        self.start_btn.pack(fill=tk.X, pady=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="⏹ 停止偵測", 
                                   command=self.stop_detection, 
                                   state=tk.DISABLED, width=20)
        self.stop_btn.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="📸 擷取畫面", 
                  command=self.capture_frame, width=20).pack(fill=tk.X, pady=5)
        
        ttk.Separator(btn_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="💾 儲存所有設定", 
                  command=self.save_all_settings, width=20).pack(fill=tk.X, pady=5)
        
        ttk.Separator(btn_frame, orient='horizontal').pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="💾 配置另存新檔", 
                  command=self.save_config, width=20).pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="📂 載入配置", 
                  command=self.load_config_file, width=20).pack(fill=tk.X, pady=5)
    
    def setup_calibration_tab(self, parent):
        """設定智慧校準分頁"""
        # 說明
        info_frame = ttk.LabelFrame(parent, text="智慧校準說明", padding="10")
        info_frame.pack(fill=tk.X, pady=5)
        
        info_text = """
📐 智慧校準步驟:
1. 啟動偵測
2. 站在已知距離處(建議150-300cm)
3. 直接點擊畫面上的偵測框
4. 輸入實際距離即可自動校準!
        """
        ttk.Label(info_frame, text=info_text, justify=tk.LEFT, 
                 foreground="blue").pack()
        
        # 快速校準 (自動帶入)
        quick_frame = ttk.LabelFrame(parent, text="快速校準", padding="10")
        quick_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(quick_frame, text="實際距離(cm):").grid(row=0, column=0, sticky=tk.W)
        self.calib_distance_var = tk.DoubleVar(value=200.0)
        ttk.Entry(quick_frame, textvariable=self.calib_distance_var, width=15).grid(
            row=0, column=1, padx=5)
        
        ttk.Label(quick_frame, text="偵測框高度(像素):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.calib_height_var = tk.DoubleVar(value=0.0)
        self.calib_height_entry = ttk.Entry(quick_frame, textvariable=self.calib_height_var, 
                                            width=15, state='readonly')
        self.calib_height_entry.grid(row=1, column=1, padx=5)
        
        ttk.Label(quick_frame, text="📌 點擊畫面上的人即可自動帶入", 
                 foreground="green", font=("Arial", 9, "italic")).grid(
            row=2, column=0, columnspan=2, pady=5)
        
        calib_btn_frame = ttk.Frame(quick_frame)
        calib_btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(calib_btn_frame, text="執行快速校準", 
                  command=self.quick_calibration).pack(side=tk.LEFT, padx=5)
        ttk.Button(calib_btn_frame, text="💾 儲存焦距", 
                  command=self.save_focal_length).pack(side=tk.LEFT, padx=5)
        
        # 多點校準
        multi_frame = ttk.LabelFrame(parent, text="多點精確校準", padding="10")
        multi_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(multi_frame, text="測量點列表:").pack(anchor=tk.W)
        
        # 測量點列表
        list_frame = ttk.Frame(multi_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.measurement_listbox = tk.Listbox(list_frame, height=6)
        self.measurement_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, 
                                 command=self.measurement_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.measurement_listbox.config(yscrollcommand=scrollbar.set)
        
        # 按鈕
        multi_btn_frame = ttk.Frame(multi_frame)
        multi_btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(multi_btn_frame, text="添加測量點", 
                  command=self.add_measurement).pack(side=tk.LEFT, padx=5)
        ttk.Button(multi_btn_frame, text="清除列表", 
                  command=self.clear_measurements).pack(side=tk.LEFT, padx=5)
        ttk.Button(multi_btn_frame, text="計算焦距", 
                  command=self.multi_calibration).pack(side=tk.LEFT, padx=5)
        ttk.Button(multi_btn_frame, text="💾 儲存焦距", 
                  command=self.save_focal_length).pack(side=tk.LEFT, padx=5)
        
        # 當前焦距顯示
        result_frame = ttk.Frame(multi_frame)
        result_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(result_frame, text="當前焦距:").pack(side=tk.LEFT)
        self.focal_length_label = ttk.Label(result_frame, 
                                           text=f"{self.config['distance']['focal_length']:.2f} 像素",
                                           font=("Arial", 12, "bold"),
                                           foreground="blue")
        self.focal_length_label.pack(side=tk.LEFT, padx=10)
        
        # 儲存所有設定按鈕
        ttk.Separator(parent, orient='horizontal').pack(fill=tk.X, pady=10)
        ttk.Button(parent, text="💾 儲存所有設定", 
                  command=self.save_all_settings, width=30).pack(pady=10)
    
    def setup_settings_tab(self, parent):
        """設定參數分頁"""
        # 建立滾動區域
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 模型參數
        model_frame = ttk.LabelFrame(scrollable_frame, text="模型參數", padding="10")
        model_frame.pack(fill=tk.X, pady=5, padx=5)
        
        self.conf_var = tk.DoubleVar(value=self.config["model"]["conf"])
        self.iou_var = tk.DoubleVar(value=self.config["model"]["iou"])
        self.imgsz_var = tk.IntVar(value=self.config["model"]["imgsz"])
        self.vid_stride_var = tk.IntVar(value=self.config["model"]["vid_stride"])
        
        ttk.Label(model_frame, text="信心閾值:").grid(row=0, column=0, sticky=tk.W)
        ttk.Scale(model_frame, from_=0.1, to=0.9, variable=self.conf_var, 
                 orient=tk.HORIZONTAL, length=200).grid(row=0, column=1)
        ttk.Label(model_frame, textvariable=self.conf_var).grid(row=0, column=2, padx=5)
        
        ttk.Label(model_frame, text="IoU 閾值:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Scale(model_frame, from_=0.1, to=0.9, variable=self.iou_var, 
                 orient=tk.HORIZONTAL, length=200).grid(row=1, column=1)
        ttk.Label(model_frame, textvariable=self.iou_var).grid(row=1, column=2, padx=5)
        
        ttk.Label(model_frame, text="影像尺寸:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Combobox(model_frame, textvariable=self.imgsz_var, 
                    values=[320, 416, 640], width=10).grid(row=2, column=1, sticky=tk.W)
        
        ttk.Label(model_frame, text="跳幀數:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(model_frame, from_=1, to=10, textvariable=self.vid_stride_var, 
                   width=10).grid(row=3, column=1, sticky=tk.W)
        
        # 距離參數
        distance_frame = ttk.LabelFrame(scrollable_frame, text="距離參數", padding="10")
        distance_frame.pack(fill=tk.X, pady=5, padx=5)
        
        self.person_height_var = tk.IntVar(
            value=self.config["distance"]["real_person_height"])
        self.adaptive_height_var = tk.BooleanVar(
            value=self.config["distance"]["use_adaptive_height"])
        self.smoothing_var = tk.BooleanVar(
            value=self.config["distance"]["use_smoothing"])
        self.display_smoothing_var = tk.BooleanVar(
            value=self.config["distance"].get("use_display_smoothing", True))
        
        ttk.Label(distance_frame, text="平均人體高度(cm):").grid(
            row=0, column=0, sticky=tk.W)
        ttk.Spinbox(distance_frame, from_=150, to=200, 
                   textvariable=self.person_height_var, width=10).grid(
            row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Checkbutton(distance_frame, text="啟用自適應高度(姿態判斷)", 
                       variable=self.adaptive_height_var).grid(
            row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Checkbutton(distance_frame, text="啟用數據平滑化(移動平均)", 
                       variable=self.smoothing_var).grid(
            row=2, column=0, columnspan=2, sticky=tk.W)
        
        ttk.Checkbutton(distance_frame, text="啟用顯示平滑化(消除跳動)", 
                       variable=self.display_smoothing_var).grid(
            row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # 平滑參數
        smooth_param_frame = ttk.Frame(distance_frame)
        smooth_param_frame.grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=20)
        
        ttk.Label(smooth_param_frame, text="平滑強度:").grid(row=0, column=0, sticky=tk.W)
        self.smooth_factor_var = tk.DoubleVar(
            value=self.config["distance"].get("display_smooth_factor", 0.3))
        ttk.Scale(smooth_param_frame, from_=0.1, to=0.9, 
                 variable=self.smooth_factor_var, 
                 orient=tk.HORIZONTAL, length=150).grid(row=0, column=1)
        ttk.Label(smooth_param_frame, text="(越小越平滑)").grid(row=0, column=2, padx=5)
        
        # 運行參數
        runtime_frame = ttk.LabelFrame(scrollable_frame, text="運行參數", padding="10")
        runtime_frame.pack(fill=tk.X, pady=5, padx=5)
        
        self.max_hours_var = tk.IntVar(
            value=self.config["runtime"]["max_runtime_hours"])
        self.auto_reconnect_var = tk.BooleanVar(
            value=self.config["runtime"]["auto_reconnect"])
        
        ttk.Label(runtime_frame, text="最大運行時間(小時):").grid(
            row=0, column=0, sticky=tk.W)
        ttk.Spinbox(runtime_frame, from_=1, to=24, 
                   textvariable=self.max_hours_var, width=10).grid(
            row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Checkbutton(runtime_frame, text="自動重新連接", 
                       variable=self.auto_reconnect_var).grid(
            row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # 儲存按鈕
        save_btn_frame = ttk.Frame(scrollable_frame)
        save_btn_frame.pack(pady=20)
        
        ttk.Button(save_btn_frame, text="💾 儲存所有設定", 
                  command=self.save_all_settings, 
                  width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(save_btn_frame, text="套用 (不儲存)", 
                  command=self.apply_settings, 
                  width=20).pack(side=tk.LEFT, padx=5)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def setup_stats_tab(self, parent):
        """設定統計資訊分頁"""
        stats_frame = ttk.Frame(parent, padding="10")
        stats_frame.pack(fill=tk.BOTH, expand=True)
        
        self.stats_text = tk.Text(stats_frame, height=20, width=40, 
                                 font=("Consolas", 10))
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(stats_frame, text="重置統計", 
                  command=self.reset_stats).pack(pady=10)
        
        ttk.Button(stats_frame, text="📊 匯出統計報告", 
                  command=self.export_stats).pack(pady=5)
    
    def on_canvas_click(self, event):
        """點擊畫布取樣偵測框高度"""
        if not self.detector_running or self.current_results is None:
            return
        
        # 轉換座標 (畫布座標 -> 實際影像座標)
        canvas_x, canvas_y = event.x, event.y
        
        # 計算縮放比例
        if self.current_frame is not None:
            frame_height, frame_width = self.current_frame.shape[:2]
            scale_x = frame_width / 800
            scale_y = frame_height / 600
            
            img_x = canvas_x * scale_x
            img_y = canvas_y * scale_y
            
            # 尋找點擊位置的偵測框
            if self.current_results[0].boxes is not None:
                for box in self.current_results[0].boxes:
                    xyxy = box.xyxy[0].cpu().numpy()
                    x1, y1, x2, y2 = xyxy
                    
                    # 檢查點擊是否在框內
                    if x1 <= img_x <= x2 and y1 <= img_y <= y2:
                        box_height = y2 - y1
                        self.calib_height_var.set(round(box_height, 1))
                        messagebox.showinfo("已取樣", 
                            f"已自動帶入偵測框高度: {box_height:.1f} 像素\n"
                            f"請輸入實際距離後點擊「執行快速校準」")
                        return
            
            messagebox.showwarning("提示", "請點擊偵測框內的位置")
    
    def toggle_fps_limit(self):
        """切換 FPS 限制"""
        if "performance" not in self.config:
            self.config["performance"] = {}
        self.config["performance"]["use_fps_limit"] = self.use_fps_limit_var.get()
    
    def load_model(self):
        """載入 YOLO 模型"""
        try:
            model_path = self.config["model"]["model_path"]
            self.update_status(f"正在載入模型: {model_path}")
            self.model = YOLO(model_path)
            self.update_status(f"✓ 模型載入成功")
        except Exception as e:
            messagebox.showerror("錯誤", f"載入模型失敗:\n{str(e)}")
            self.update_status(f"❌ 模型載入失敗")
    
    def start_detection(self):
        """啟動偵測"""
        if self.detector_running:
            return
        
        if self.model is None:
            messagebox.showwarning("警告", "模型尚未載入")
            return
        
        # 開啟攝影機
        try:
            source = self.source_var.get()
            if source.isdigit():
                source = int(source)
            
            self.cap = cv2.VideoCapture(source)
            if not self.cap.isOpened():
                raise Exception(f"無法開啟影像來源: {source}")
            
            # 設定解析度
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width_var.get())
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height_var.get())
            
            self.detector_running = True
            self.start_time = time.time()
            self.total_detections = 0
            self.frame_times.clear()
            
            # 重置距離計算器
            self.distance_calculator = DistanceCalculator(self.config)
            
            # 啟動偵測執行緒
            self.detection_thread = threading.Thread(target=self.detection_loop, daemon=True)
            self.detection_thread.start()
            
            # 更新按鈕狀態
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            
            self.update_status("✓ 偵測已啟動")
            
        except Exception as e:
            messagebox.showerror("錯誤", f"啟動失敗:\n{str(e)}")
            self.detector_running = False
    
    def stop_detection(self):
        """停止偵測"""
        self.detector_running = False
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        # 更新按鈕狀態
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        self.update_status("⏹ 偵測已停止")
    
    def detection_loop(self):
        """偵測主迴圈"""
        frame_count = 0
        fps_start = time.time()
        fps_counter = 0
        last_frame_time = time.time()
        
        # FPS 限制參數
        use_fps_limit = self.config.get("performance", {}).get("use_fps_limit", False)
        target_fps = self.config.get("performance", {}).get("target_fps", 30)
        frame_interval = 1.0 / target_fps if use_fps_limit else 0
        
        while self.detector_running:
            loop_start = time.time()
            
            ret, frame = self.cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # 跳幀處理
            if frame_count % self.config["model"]["vid_stride"] != 0:
                continue
            
            try:
                # YOLO 偵測
                results = self.model.track(
                    source=frame,
                    classes=[0],
                    conf=self.config["model"]["conf"],
                    iou=self.config["model"]["iou"],
                    imgsz=self.config["model"]["imgsz"],
                    device=self.config["model"]["device"],
                    tracker=self.config["model"]["tracker"],
                    persist=True,
                    show=False,
                    verbose=False
                )
                
                self.current_results = results  # 儲存結果供點擊取樣使用
                
                # 處理結果
                annotated_frame = results[0].plot(conf=True, labels=True, boxes=True)
                
                # 計算距離
                if results[0].boxes is not None:
                    distances = []
                    for box in results[0].boxes:
                        xyxy = box.xyxy[0].cpu().numpy()
                        box_height = xyxy[3] - xyxy[1]
                        box_width = xyxy[2] - xyxy[0]
                        
                        # 取得追蹤ID
                        track_id = int(box.id[0]) if box.id is not None else None
                        
                        # 計算距離
                        distance = self.distance_calculator.calculate_distance(
                            box_height, box_width, track_id)
                        distances.append(distance)
                        
                        # 顯示距離
                        x1, y1 = int(xyxy[0]), int(xyxy[1])
                        color = self.get_distance_color(distance)
                        cv2.putText(annotated_frame, f"{distance:.1f}cm", 
                                   (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                                   0.6, color, 2)
                    
                    self.total_detections = len(results[0].boxes)
                    self.closest_distance = min(distances) if distances else 0
                else:
                    self.total_detections = 0
                    self.closest_distance = 0
                
                # 計算 FPS
                fps_counter += 1
                if time.time() - fps_start >= 1.0:
                    self.fps = fps_counter
                    fps_counter = 0
                    fps_start = time.time()
                
                # 計算實際 FPS (包含處理時間)
                frame_time = time.time() - last_frame_time
                self.frame_times.append(frame_time)
                if len(self.frame_times) > 0:
                    avg_frame_time = np.mean(self.frame_times)
                    self.actual_fps = int(1.0 / avg_frame_time) if avg_frame_time > 0 else 0
                last_frame_time = time.time()
                
                # 在影像上顯示資訊
                elapsed = time.time() - self.start_time
                hours = int(elapsed // 3600)
                minutes = int((elapsed % 3600) // 60)
                seconds = int(elapsed % 60)
                
                cv2.putText(annotated_frame, f"FPS: {self.fps}/{self.actual_fps}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(annotated_frame, f"人數: {self.total_detections}", 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                if self.closest_distance > 0:
                    cv2.putText(annotated_frame, f"最近: {self.closest_distance:.1f}cm", 
                               (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                cv2.putText(annotated_frame, f"運行: {hours:02d}:{minutes:02d}:{seconds:02d}", 
                           (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                self.current_frame = annotated_frame
                
                # 更新顯示
                self.root.after(0, self.update_display, annotated_frame)
                self.root.after(0, self.update_status_display)
                
                # FPS 限制
                if use_fps_limit:
                    elapsed_time = time.time() - loop_start
                    sleep_time = frame_interval - elapsed_time
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                
            except Exception as e:
                print(f"偵測錯誤: {e}")
                continue
    
    def get_distance_color(self, distance):
        """根據距離返回顏色"""
        if distance > 300:
            return (0, 255, 0)  # 綠色
        elif distance > 150:
            return (0, 255, 255)  # 黃色
        else:
            return (0, 0, 255)  # 紅色
    
    def update_display(self, frame):
        """更新顯示畫面"""
        try:
            # 調整大小以符合畫布
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_resized = cv2.resize(frame_rgb, (800, 600))
            
            img = Image.fromarray(frame_resized)
            imgtk = ImageTk.PhotoImage(image=img)
            
            self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
            self.canvas.imgtk = imgtk
        except Exception as e:
            print(f"更新顯示錯誤: {e}")
    
    def update_status_display(self):
        """更新狀態顯示"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        
        status = f"""
╔═════════════════════════════════════════════════════════════════════╗
║  FPS: {self.fps:3d}/{self.actual_fps:3d}  |  偵測人數: {self.total_detections:2d}  |  最近距離: {self.closest_distance:6.1f} cm
║  運行時間: {hours:02d}:{minutes:02d}  |  焦距: {self.config['distance']['focal_length']:.1f} px
╚═════════════════════════════════════════════════════════════════════╝
        """
        
        self.status_text.delete(1.0, tk.END)
        self.status_text.insert(1.0, status.strip())
        
        # 更新實際 FPS 標籤
        self.actual_fps_label.config(text=str(self.actual_fps))
    
    def update_status(self, message):
        """更新狀態訊息"""
        print(message)
    
    def capture_frame(self):
        """擷取當前畫面"""
        if self.current_frame is not None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{timestamp}.jpg"
            cv2.imwrite(filename, self.current_frame)
            messagebox.showinfo("成功", f"畫面已儲存:\n{filename}")
        else:
            messagebox.showwarning("警告", "沒有可擷取的畫面")
    
    def quick_calibration(self):
        """快速校準 (自動帶入框高度)"""
        try:
            distance = self.calib_distance_var.get()
            height = self.calib_height_var.get()
            
            if height == 0:
                messagebox.showwarning("提示", "請先點擊畫面上的偵測框來取樣高度")
                return
            
            focal_length = self.distance_calculator.calibrate_focal_length(height, distance)
            self.focal_length_label.config(text=f"{focal_length:.2f} 像素")
            messagebox.showinfo("成功", f"焦距已校準為:\n{focal_length:.2f} 像素")
            
        except Exception as e:
            messagebox.showerror("錯誤", f"校準失敗:\n{str(e)}")
    
    def add_measurement(self):
        """添加測量點"""
        try:
            distance = self.calib_distance_var.get()
            height = self.calib_height_var.get()
            
            if height == 0:
                messagebox.showwarning("提示", "請先點擊畫面上的偵測框來取樣高度")
                return
            
            self.calibration_measurements.append((height, distance))
            
            self.measurement_listbox.insert(tk.END, 
                f"距離: {distance:.1f}cm, 框高: {height:.1f}px")
            
            messagebox.showinfo("成功", "測量點已添加")
            
            # 重置框高度供下次測量
            self.calib_height_var.set(0.0)
            
        except Exception as e:
            messagebox.showerror("錯誤", f"添加失敗:\n{str(e)}")
    
    def clear_measurements(self):
        """清除測量點"""
        self.calibration_measurements = []
        self.measurement_listbox.delete(0, tk.END)
    
    def multi_calibration(self):
        """多點校準"""
        if len(self.calibration_measurements) < 2:
            messagebox.showwarning("警告", "至少需要2個測量點")
            return
        
        try:
            avg_focal, std_dev = self.distance_calculator.multi_point_calibration(
                self.calibration_measurements)
            
            self.focal_length_label.config(text=f"{avg_focal:.2f} 像素")
            
            quality = "優秀" if std_dev < 10 else "良好" if std_dev < 20 else "需改善"
            
            messagebox.showinfo("多點校準完成", 
                f"平均焦距: {avg_focal:.2f} 像素\n"
                f"標準差: {std_dev:.2f}\n"
                f"測量點數: {len(self.calibration_measurements)}\n"
                f"精確度: {quality}")
            
        except Exception as e:
            messagebox.showerror("錯誤", f"校準失敗:\n{str(e)}")
    
    def apply_settings(self):
        """套用設定 (不儲存到檔案)"""
        try:
            self.apply_settings_internal()
            messagebox.showinfo("成功", "設定已套用 (未儲存至檔案)")
            
        except Exception as e:
            messagebox.showerror("錯誤", f"套用設定失敗:\n{str(e)}")
    
    def save_camera_settings(self):
        """儲存攝影機設定"""
        try:
            self.config["camera"]["source"] = int(self.source_var.get()) if self.source_var.get().isdigit() else self.source_var.get()
            self.config["camera"]["width"] = self.width_var.get()
            self.config["camera"]["height"] = self.height_var.get()
            
            if ConfigManager.save_config(self.config, self.config_path):
                messagebox.showinfo("成功", "攝影機設定已儲存至 sensor_config.json")
            else:
                messagebox.showerror("錯誤", "儲存失敗")
        except Exception as e:
            messagebox.showerror("錯誤", f"儲存失敗:\n{str(e)}")
    
    def save_performance_settings(self):
        """儲存效能設定"""
        try:
            if "performance" not in self.config:
                self.config["performance"] = {}
            self.config["performance"]["use_fps_limit"] = self.use_fps_limit_var.get()
            self.config["performance"]["target_fps"] = self.target_fps_var.get()
            
            if ConfigManager.save_config(self.config, self.config_path):
                messagebox.showinfo("成功", "效能設定已儲存至 sensor_config.json")
            else:
                messagebox.showerror("錯誤", "儲存失敗")
        except Exception as e:
            messagebox.showerror("錯誤", f"儲存失敗:\n{str(e)}")
    
    def save_focal_length(self):
        """儲存焦距設定"""
        try:
            if ConfigManager.save_config(self.config, self.config_path):
                messagebox.showinfo("成功", 
                    f"焦距 {self.config['distance']['focal_length']:.2f} 已儲存至 sensor_config.json")
            else:
                messagebox.showerror("錯誤", "儲存失敗")
        except Exception as e:
            messagebox.showerror("錯誤", f"儲存失敗:\n{str(e)}")
    
    def save_all_settings(self):
        """儲存所有設定"""
        try:
            # 先套用設定
            self.apply_settings_internal()
            
            # 儲存到 sensor_config.json
            if ConfigManager.save_config(self.config, self.config_path):
                messagebox.showinfo("成功", "所有設定已儲存至 sensor_config.json")
            else:
                messagebox.showerror("錯誤", "儲存失敗")
        except Exception as e:
            messagebox.showerror("錯誤", f"儲存失敗:\n{str(e)}")
    
    def apply_settings_internal(self):
        """內部套用設定方法 (不顯示訊息)"""
        self.config["model"]["conf"] = self.conf_var.get()
        self.config["model"]["iou"] = self.iou_var.get()
        self.config["model"]["imgsz"] = self.imgsz_var.get()
        self.config["model"]["vid_stride"] = self.vid_stride_var.get()
        
        self.config["distance"]["real_person_height"] = self.person_height_var.get()
        self.config["distance"]["use_adaptive_height"] = self.adaptive_height_var.get()
        self.config["distance"]["use_smoothing"] = self.smoothing_var.get()
        self.config["distance"]["use_display_smoothing"] = self.display_smoothing_var.get()
        self.config["distance"]["display_smooth_factor"] = self.smooth_factor_var.get()
        
        if "performance" not in self.config:
            self.config["performance"] = {}
        self.config["performance"]["use_fps_limit"] = self.use_fps_limit_var.get()
        self.config["performance"]["target_fps"] = self.target_fps_var.get()
        
        self.config["runtime"]["max_runtime_hours"] = self.max_hours_var.get()
        self.config["runtime"]["auto_reconnect"] = self.auto_reconnect_var.get()
        
        # 更新距離計算器
        self.distance_calculator.config = self.config
    
    def save_config(self):
        """儲存配置 (另存新檔)"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=self.config_path
        )
        
        if filename:
            if ConfigManager.save_config(self.config, filename):
                messagebox.showinfo("成功", f"配置已儲存至:\n{filename}")
            else:
                messagebox.showerror("錯誤", "儲存失敗")
    
    def load_config_file(self):
        """載入配置檔"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            self.config = ConfigManager.load_config(filename)
            self.config_path = filename
            self.update_ui_from_config()
            messagebox.showinfo("成功", f"配置已載入:\n{filename}")
    
    def update_ui_from_config(self):
        """從配置更新 UI"""
        self.source_var.set(str(self.config["camera"]["source"]))
        self.width_var.set(self.config["camera"]["width"])
        self.height_var.set(self.config["camera"]["height"])
        
        self.conf_var.set(self.config["model"]["conf"])
        self.iou_var.set(self.config["model"]["iou"])
        self.imgsz_var.set(self.config["model"]["imgsz"])
        self.vid_stride_var.set(self.config["model"]["vid_stride"])
        
        self.person_height_var.set(self.config["distance"]["real_person_height"])
        self.adaptive_height_var.set(self.config["distance"]["use_adaptive_height"])
        self.smoothing_var.set(self.config["distance"]["use_smoothing"])
        self.display_smoothing_var.set(
            self.config["distance"].get("use_display_smoothing", True))
        self.smooth_factor_var.set(
            self.config["distance"].get("display_smooth_factor", 0.3))
        
        if "performance" in self.config:
            self.use_fps_limit_var.set(self.config["performance"].get("use_fps_limit", False))
            self.target_fps_var.set(self.config["performance"].get("target_fps", 30))
        
        self.max_hours_var.set(self.config["runtime"]["max_runtime_hours"])
        self.auto_reconnect_var.set(self.config["runtime"]["auto_reconnect"])
        
        self.focal_length_label.config(
            text=f"{self.config['distance']['focal_length']:.2f} 像素")
    
    def reset_stats(self):
        """重置統計"""
        self.start_time = time.time()
        self.total_detections = 0
        self.closest_distance = 0
        self.frame_times.clear()
        messagebox.showinfo("成功", "統計已重置")
    
    def export_stats(self):
        """匯出統計報告"""
        if self.start_time is None:
            messagebox.showwarning("警告", "尚未開始偵測")
            return
        
        elapsed = time.time() - self.start_time
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        
        report = f"""
YOLO11n 距離偵測系統 - 統計報告
生成時間: {time.strftime("%Y-%m-%d %H:%M:%S")}
{'='*50}

運行資訊:
- 運行時間: {hours}小時 {minutes}分鐘
- 平均 FPS: {self.fps}
- 實際 FPS: {self.actual_fps}

偵測統計:
- 當前偵測人數: {self.total_detections}
- 最近距離: {self.closest_distance:.1f} cm

系統配置:
- 焦距: {self.config['distance']['focal_length']:.2f} 像素
- 人體高度: {self.config['distance']['real_person_height']} cm
- 自適應高度: {'啟用' if self.config['distance']['use_adaptive_height'] else '停用'}
- 數據平滑化: {'啟用' if self.config['distance']['use_smoothing'] else '停用'}
- 顯示平滑化: {'啟用' if self.config['distance'].get('use_display_smoothing') else '停用'}
- FPS 限制: {'啟用' if self.config.get('performance', {}).get('use_fps_limit') else '停用'}

模型參數:
- 信心閾值: {self.config['model']['conf']}
- IoU 閾值: {self.config['model']['iou']}
- 影像尺寸: {self.config['model']['imgsz']}
- 跳幀數: {self.config['model']['vid_stride']}
"""
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"stats_{time.strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report)
                messagebox.showinfo("成功", f"統計報告已匯出:\n{filename}")
            except Exception as e:
                messagebox.showerror("錯誤", f"匯出失敗:\n{str(e)}")
    
    def on_closing(self):
        """關閉程式"""
        if messagebox.askokcancel("離開", "確定要離開嗎?"):
            self.stop_detection()
            self.root.destroy()


def main():
    """主程式"""
    root = tk.Tk()
    app = YOLO11DistanceDetectorGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
