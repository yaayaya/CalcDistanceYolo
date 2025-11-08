# 🎯 YOLO11 距離偵測 FastAPI 專案

基於 YOLO11n 的即時人體距離偵測系統,提供 WebSocket 即時串流和 RESTful API,適用於展覽互動作品。

## 📁 專案結構

```
Test/
├── app/                          # FastAPI 應用
│   ├── models/                   # Pydantic 資料模型
│   │   └── schemas.py
│   ├── services/                 # 核心服務
│   │   ├── calculator.py         # 距離計算器
│   │   ├── detector.py           # YOLO 偵測服務
│   │   └── connection_manager.py # WebSocket 管理
│   ├── api/                      # API 端點
│   │   ├── websocket.py          # WebSocket 路由
│   │   └── frontend.py           # RESTful API
│   └── utils/                    # 工具函式
│       └── config_loader.py      # 配置載入器
├── admin/                        # 管理後台
│   ├── index.html
│   ├── style.css
│   └── script.js
├── configs/                      # 配置檔案資料夾
│   └── network_config.json       # 網路設定 (後台可修改)
├── 基本偵測/                      # GUI 工具資料夾
│   └── camera_test_gui_v2.py     # 參數校準工具
├── sensor_config.json            # 感測器配置 (GUI 工具修改)
├── yolo11n.pt                    # YOLO 模型檔案
├── main.py                       # FastAPI 主程式
├── requirements.txt              # Python 依賴套件
└── README.md                     # 專案說明
```

## 🚀 快速開始

### 1. 安裝依賴套件

```powershell
pip install -r requirements.txt
```

### 2. 校準焦距參數 (首次使用)

使用 GUI 工具進行焦距校準:

```powershell
cd 基本偵測
python camera_test_gui_v2.py
```

**校準步驟:**
1. 啟動偵測
2. 站在已知距離處 (建議 150-300cm)
3. 點擊畫面上的人物偵測框
4. 輸入實際距離並執行校準
5. 儲存設定 (自動更新 `sensor_config.json`)

### 3. 啟動 FastAPI 服務

```powershell
cd ..
python main.py
```

或使用 uvicorn:

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 存取服務

- **管理後台**: http://localhost:8000/admin
- **API 文件**: http://localhost:8000/docs
- **健康檢查**: http://localhost:8000/health

## 📡 API 端點

### WebSocket 端點

#### 1. 完整偵測串流 (後台監控用)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/detection');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(data);
    /*
    {
        "detections": [
            {
                "track_id": 1,
                "distance": 185.3,
                "bbox": [120.5, 80.2, 250.8, 420.6],
                "confidence": 0.92
            }
        ],
        "fps": 30,
        "actual_fps": 28,
        "closest_distance": 185.3,
        "total_count": 1,
        "timestamp": 1699459200.123
    }
    */
};
```

#### 2. 簡化版串流 (前端展覽作品用)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/live');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(data);
    /*
    {
        "closest_distance": 185.3,
        "total_count": 1,
        "timestamp": 1699459200.123
    }
    */
};
```

### RESTful API 端點

#### 1. 取得當前距離資料

```http
GET /api/distance/current
```

**回應範例:**
```json
{
    "status": "success",
    "message": "成功取得當前距離資料",
    "data": {
        "detections": [...],
        "closest_distance": 185.3,
        "total_count": 1,
        "fps": 30
    },
    "timestamp": 1699459200.123
}
```

#### 2. 取得統計資訊

```http
GET /api/detection/stats
```

**回應範例:**
```json
{
    "status": "success",
    "data": {
        "total_count": 1,
        "closest_distance": 185.3,
        "fps": 30,
        "actual_fps": 28,
        "is_running": true,
        "uptime": 3600
    }
}
```

#### 3. 取得網路配置

```http
GET /api/network-config
```

#### 4. 更新網路配置

```http
PUT /api/network-config
Content-Type: application/json

{
    "websocket": {
        "host": "0.0.0.0",
        "port": 8000,
        "broadcast_interval": 33
    }
}
```

#### 5. 重啟偵測器

```http
POST /api/detector/refresh
```

用於在 GUI 工具修改 `sensor_config.json` 後重新載入配置。

## 🎛️ 管理後台使用說明

存取 http://localhost:8000/admin

### 功能區塊

1. **即時監控**
   - 偵測人數
   - 最近距離 (含顏色標示: >300cm 綠色 / 150-300cm 黃色 / <150cm 紅色)
   - FPS (目標/實際)
   - 運行時間

2. **網路設定**
   - 廣播間隔 (建議 33ms ≈ 30 FPS)
   - WebSocket 主機/埠號
   - 修改後需手動刷新連線

3. **控制面板**
   - 🔄 刷新 WebSocket 連線 - 套用新的網路設定
   - 🔁 重啟偵測器 - 重新載入 `sensor_config.json`
   - 📖 查看 API 文件

## 📝 配置檔案說明

### sensor_config.json (感測器配置)

由 `camera_test_gui_v2.py` 管理,FastAPI 只讀取不修改。

**主要參數:**
- `model`: YOLO 模型設定 (model_path, imgsz, conf, iou, device...)
- `distance`: 距離計算參數 (focal_length, real_person_height, smoothing...)
- `camera`: 攝影機設定 (source, width, height)
- `performance`: 效能設定 (use_fps_limit, target_fps)

### network_config.json (網路配置)

透過後台 API 修改。

**參數說明:**
```json
{
  "websocket": {
    "host": "0.0.0.0",              // WebSocket 主機 (本地執行固定)
    "port": 8000,                   // WebSocket 埠號
    "broadcast_interval": 33        // 廣播間隔 (毫秒, 33 ≈ 30 FPS)
  }
}
```

## 🎨 前端展覽作品串接範例

### 使用 WebSocket (即時推送)

```html
<!DOCTYPE html>
<html>
<head>
    <title>展覽作品 - 距離互動</title>
</head>
<body>
    <h1>最近距離: <span id="distance">--</span> cm</h1>
    <h2>偵測人數: <span id="count">0</span></h2>

    <script>
        const ws = new WebSocket('ws://localhost:8000/ws/live');
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            // 更新顯示
            document.getElementById('distance').textContent = 
                data.closest_distance.toFixed(1);
            document.getElementById('count').textContent = 
                data.total_count;
            
            // 根據距離觸發互動效果
            if (data.closest_distance < 150) {
                document.body.style.background = 'red';
            } else if (data.closest_distance < 300) {
                document.body.style.background = 'yellow';
            } else {
                document.body.style.background = 'green';
            }
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket 錯誤:', error);
        };
    </script>
</body>
</html>
```

### 使用 REST API (輪詢方式)

```javascript
async function fetchDistance() {
    try {
        const response = await fetch('http://localhost:8000/api/distance/current');
        const result = await response.json();
        
        if (result.status === 'success') {
            const distance = result.data.closest_distance;
            const count = result.data.total_count;
            
            console.log(`距離: ${distance} cm, 人數: ${count}`);
            
            // 觸發互動邏輯...
        }
    } catch (error) {
        console.error('API 錯誤:', error);
    }
}

// 每 100ms 輪詢一次
setInterval(fetchDistance, 100);
```

## 🔧 常見問題

### Q: 距離不準確怎麼辦?

**A:** 使用 GUI 工具重新校準焦距:
1. 執行 `python 基本偵測/camera_test_gui_v2.py`
2. 進行多點校準 (建議 3-5 個距離點)
3. 儲存設定
4. 在後台點擊「重啟偵測器」

### Q: WebSocket 斷線後怎麼辦?

**A:** 後台手動點擊「刷新 WebSocket 連線」或重新整理頁面。

### Q: 如何修改攝影機來源?

**A:** 
1. 使用 GUI 工具修改 `sensor_config.json` 的 `camera.source`
2. 在後台點擊「重啟偵測器」

### Q: 支援多個前端同時連線嗎?

**A:** 目前設計為單一展覽作品使用,多連線未經測試。

### Q: 如何提高 FPS?

**A:** 
1. 降低 `sensor_config.json` 的 `model.imgsz` (如 320)
2. 增加 `model.vid_stride` (跳幀數)
3. 使用 GPU (`model.device: "cuda"`)

## 📚 技術架構

- **後端框架**: FastAPI 0.109.0
- **YOLO 模型**: Ultralytics YOLO11n
- **影像處理**: OpenCV 4.9.0
- **WebSocket**: 原生 WebSocket + FastAPI
- **前端**: 原生 HTML/CSS/JavaScript (無框架)

## 📄 授權

此專案為展覽用途開發,本地執行無安全性設定。

## 🙋 支援

如有問題請參考:
- FastAPI 文件: http://localhost:8000/docs
- Ultralytics 文件: https://docs.ultralytics.com/

---

**最後更新:** 2025-11-08  
**版本:** 1.0.0
