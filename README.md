# 🎯 YOLO11 距離偵測系統

基於 YOLO11n 的即時人體距離偵測系統,提供 WebSocket 即時串流和 RESTful API,適用於展覽互動作品。

## 📁 專案結構

```
CalcDistanceYolo/
├── backend/              # 後端服務
│   ├── app/             # FastAPI 應用程式碼
│   ├── configs/         # 網路設定檔
│   ├── main.py          # 主程式進入點
│   ├── config.json      # (已棄用)
│   └── sensor_config.json # 感測器設定檔
├── frontend/            # 前端介面
│   ├── index.html       # 管理後台
│   ├── style.css
│   └── script.js
├── models/              # YOLO 模型檔案
│   └── yolo11n.pt
├── tools/               # 輔助工具
│   └── 基本偵測/        # 焦距校準工具
├── docs/                # 專案文件
├── requirements.txt     # Python 依賴套件
└── README.md            # 本檔案
```

## 🚀 快速開始

### 1. 安裝依賴

```powershell
pip install -r requirements.txt
```

### 2. 校準焦距參數 (首次使用)

```powershell
cd tools\基本偵測
python camera_test_gui_v2.py
```

詳細校準步驟請參考 [docs/快速啟動.md](docs/快速啟動.md)

### 3. 啟動服務

```powershell
python run.py
```

或直接執行:

```powershell
cd backend
python main.py
```

### 4. 存取服務

- **管理後台**: http://localhost:8000/admin
- **API 文件**: http://localhost:8000/docs
- **健康檢查**: http://localhost:8000/health

## 📡 API 使用

### WebSocket 連線

```javascript
// 完整偵測資料 (後台監控)
const ws = new WebSocket('ws://localhost:8000/ws/detection');

// 簡化版資料 (展覽作品)
const wsLive = new WebSocket('ws://localhost:8000/ws/live');

wsLive.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('最近距離:', data.closest_distance);
    console.log('偵測人數:', data.total_count);
};
```

### REST API

```javascript
// 取得當前距離資料
const response = await fetch('http://localhost:8000/api/distance/current');
const result = await response.json();
```

## 📚 詳細文件

- [原始完整文件](docs/原始README.md)
- [快速啟動指南](docs/快速啟動.md)
- [專案規劃](docs/規劃.md)

## 🔧 設定檔案

- `backend/sensor_config.json` - 感測器與 YOLO 模型設定 (透過 GUI 工具修改)
- `backend/configs/network_config.json` - 網路與 WebSocket 設定 (透過後台 API 修改)

## 🛠️ 技術架構

- **後端框架**: FastAPI 0.109.0
- **AI 模型**: Ultralytics YOLO11n
- **影像處理**: OpenCV 4.9.0
- **WebSocket**: FastAPI WebSocket
- **前端**: 原生 HTML/CSS/JavaScript

## 📄 授權

此專案為展覽用途開發。

## 🙋 支援

遇到問題請參考:
- [API 文件](http://localhost:8000/docs) (啟動服務後可存取)
- [Ultralytics 文件](https://docs.ultralytics.com/)

---

**最後更新**: 2025-11-08  
**版本**: 1.0.0
