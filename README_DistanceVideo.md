python tools/基本偵測/camera_test_gui_v2.py

# 🎬 DistanceVideo - 距離互動影片系統

> 基於 YOLO11 人體距離偵測的創新互動影片裝置

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.0-brightgreen.svg)](https://vuejs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ 專案特色

- 🎯 **即時距離偵測**: 使用 YOLO11n 模型偵測觀眾與螢幕距離
- ⚡ **動態速度調整**: 根據距離即時調整影片播放速度(0.25x-20x)
- 🎨 **平滑過渡**: Ease-out 曲線確保速度變化自然流暢
- 👥 **多人處理**: 自動選取最近的觀眾作為控制依據
- 🖥️ **雙模式切換**: 除錯模式與展覽模式一鍵切換
- 📱 **響應式設計**: 支援桌面與行動裝置
- 🎛️ **後台管理**: 完整的參數配置與影片管理系統

## 🎥 展示效果

```
觀眾距離 → YOLO11 偵測 → 動態計算速度 → 平滑過渡播放
  50cm          ↓              10.0x           ↓
 300cm      即時追蹤            5.0x        流暢體驗
 500cm          ↓              1.0x           ↓
```

## 🚀 快速開始

### 1. 安裝相依套件

```bash
pip install -r requirements.txt
```

### 2. 啟動服務

```bash
cd backend
python main.py
```

### 3. 訪問介面

- 播放頁面: http://localhost:8000/player.html
- 後台管理: http://localhost:8000/admin.html
- API 文件: http://localhost:8000/docs

### 4. 上傳影片並開始

1. 開啟後台管理
2. 上傳影片(建議 WebM 格式)
3. 設定為主影片
4. 調整參數
5. 開啟播放頁面測試

詳細說明請參考 [快速啟動指南](docs/projectDoc/快速啟動.md)

## 📁 專案結構

```
CalcDistanceYolo/
├── backend/                 # 後端服務
│   ├── main.py             # FastAPI 主程式
│   ├── app/
│   │   ├── api/            # API 端點
│   │   │   ├── admin_api.py      # 後台管理 API
│   │   │   ├── frontend.py       # 前端 API
│   │   │   └── websocket.py      # WebSocket 串流
│   │   ├── services/       # 核心服務
│   │   │   ├── detector.py       # YOLO 偵測器
│   │   │   └── calculator.py     # 距離計算
│   │   └── models/         # 資料模型
│   └── configs/            # 配置檔案
│       ├── project_config.json   # 專案配置
│       ├── sensor_config.json    # 感應器配置
│       └── network_config.json   # 網路配置
├── frontend/               # 前端頁面
│   ├── admin.html         # 後台管理
│   ├── player.html        # 播放頁面
│   ├── css/               # 樣式表
│   ├── js/                # JavaScript
│   │   └── api-client.js        # API 客戶端
│   ├── videos/            # 影片存放
│   └── cdn/               # CDN 函式庫
├── docs/                  # 文件
│   └── projectDoc/
│       ├── DistanceVideo.md           # 規格書
│       ├── DistanceVideo_實作摘要.md   # 實作摘要
│       └── 快速啟動.md                 # 啟動指南
├── requirements.txt       # Python 套件
└── README.md             # 本檔案
```

## 🎛️ 核心功能

### 1. 距離偵測與速度控制

- ✅ 自動選取最近的人作為控制依據
- ✅ 距離越近播放越快(可反向)
- ✅ 平滑過渡機制(Ease-out 曲線)
- ✅ 距離抖動過濾
- ✅ 人臉遺失自動回復

### 2. 後台管理系統

#### 影片控制參數
- 基礎/最大/最小播放速度
- 速度轉換時間
- 反向模式切換
- 循環/靜音/自動播放

#### 距離偵測校準
- 最小/最大距離設定
- 距離變化閾值
- 平滑係數調整
- 啟動/停用延遲

#### 顯示模式控制
- 除錯模式開關
- 展覽模式開關
- 資訊顯示項目
- 游標隱藏延遲

#### 影片管理
- 影片上傳(MP4/WebM/OGG)
- 影片列表查看
- 主影片設定
- 影片刪除

### 3. 播放頁面功能

#### 除錯模式
- 播放速度顯示
- 偵測距離顯示(含顏色警示)
- 人臉數量顯示
- FPS 顯示
- 連線狀態顯示
- 運行時間顯示

#### 展覽模式
- 全螢幕播放
- 隱藏所有 UI 元素
- 自動隱藏游標

#### 快捷鍵
- `Ctrl+Shift+D`: 切換除錯模式
- `Ctrl+Shift+E`: 切換展覽模式

## 🎨 使用場景

### 藝術展覽
觀眾靠近時影片加速播放,創造動態互動體驗

### 博物館導覽
根據觀眾距離調整內容呈現節奏

### 商業展示
吸引觀眾靠近觀看,提升互動參與度

### 裝置藝術
結合空間與時間的創新表現形式

## 📊 技術架構

### 後端
- **框架**: FastAPI
- **偵測**: YOLO11n (Ultralytics)
- **串流**: WebSocket
- **配置**: JSON

### 前端
- **框架**: Vue.js 3 (CDN)
- **HTTP**: Axios
- **樣式**: 原生 CSS
- **動畫**: requestAnimationFrame

### 演算法
- **距離計算**: 焦距法(Focal Length Method)
- **速度映射**: 線性插值(Linear Interpolation)
- **平滑過渡**: Ease-out 三次曲線
- **資料過濾**: 移動平均(Moving Average)

## ⚙️ 配置說明

### 建議參數

#### 正常展示
```json
{
  "baseSpeed": 1.0,
  "maxSpeed": 10.0,
  "minDistance": 50,
  "maxDistance": 500,
  "transitionTime": 500
}
```

#### 快速反應
```json
{
  "baseSpeed": 2.0,
  "maxSpeed": 15.0,
  "transitionTime": 300,
  "smoothingFactor": 0.2
}
```

#### 平滑體驗
```json
{
  "transitionTime": 1000,
  "smoothingFactor": 0.5,
  "distanceThreshold": 20
}
```

## 🎬 影片建議

### 格式
- **推薦**: WebM (VP9 編碼)
- **解析度**: 1920x1080
- **位元率**: 5-8 Mbps
- **大小**: < 500MB

### 內容
- ✅ 敘事性影片
- ✅ 風景縮時
- ✅ 抽象動畫
- ❌ 文字密集
- ❌ 音訊同步要求高

## 🔧 開發指南

### API 端點

```
GET  /api/admin/config              取得配置
PUT  /api/admin/config              更新配置
POST /api/admin/config/reset        重置配置
GET  /api/admin/videos              影片列表
POST /api/admin/videos/upload       上傳影片
DEL  /api/admin/videos/{filename}   刪除影片
PUT  /api/admin/videos/current/{f}  設定主影片
WS   /ws/detection                  距離偵測串流
```

### 自訂開發

1. 修改距離計算邏輯: `backend/app/services/calculator.py`
2. 調整偵測參數: `backend/configs/sensor_config.json`
3. 自訂 UI 樣式: `frontend/css/player.css`
4. 新增 API 端點: `backend/app/api/admin_api.py`

## 📈 效能優化

### 前端
- ✅ requestAnimationFrame 同步繪製
- ✅ GPU 加速(transform, will-change)
- ✅ 事件節流與防抖
- ✅ 記憶體管理(定時器清理)
- ✅ WebSocket 自動重連

### 後端
- ✅ 非同步處理(async/await)
- ✅ 連線池管理
- ✅ 影片串流優化
- ✅ 錯誤處理機制

### 長時間運行
- ✅ 8小時穩定測試
- ✅ 記憶體洩漏檢測
- ✅ 自動錯誤恢復
- ✅ 健康檢查機制

## 🐛 故障排除

### 常見問題

**Q: 影片無法播放?**  
A: 檢查是否設定主影片、格式支援、瀏覽器控制台錯誤

**Q: 距離偵測無反應?**  
A: 檢查 WebSocket 連線、攝影機狀態、sensor_config.json

**Q: 速度變化太突兀?**  
A: 增加轉換時間(500-1000ms)、提高平滑係數(0.3-0.5)

詳細請參考 [快速啟動指南](docs/projectDoc/快速啟動.md)

## 📝 授權

MIT License - 詳見 [LICENSE](LICENSE) 檔案

## 👥 貢獻

歡迎提交 Issue 和 Pull Request!

## 📞 聯絡

- 專案文件: `docs/projectDoc/`
- API 文件: http://localhost:8000/docs
- Issue: [GitHub Issues](https://github.com/yaayaya/CalcDistanceYolo/issues)

---

**建立日期**: 2025-01-09  
**版本**: v1.0.0  
**狀態**: ✅ 完整實作完成

Made with ❤️ by DistanceVideo Team
