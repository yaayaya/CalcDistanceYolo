# DistanceVideo 專案實作完成

## 專案概述

DistanceVideo 是一個創新的多媒體互動裝置系統,能夠根據觀眾與螢幕的距離,透過 YOLO11 人體距離偵測技術即時動態調整影片播放速度(0.25x～20x)。

## 已完成功能

### ✅ 1. 後端 API 系統

#### 專案配置管理 (`backend/configs/project_config.json`)
- **影片控制參數**: baseSpeed, maxSpeed, minSpeed, loop, muted, autoplay, transitionTime, reverseMode
- **距離偵測校準**: minDistance, maxDistance, distanceThreshold, smoothingFactor, 延遲設定
- **顯示模式控制**: debugMode, exhibitionMode, 各項顯示開關
- **快速預設**: 正常模式、快速模式、慢速模式、展示模式

#### Admin API 端點 (`backend/app/api/admin_api.py`)
- `GET /api/admin/config` - 取得專案配置
- `PUT /api/admin/config` - 更新配置(部分更新)
- `POST /api/admin/config/reset` - 重置為預設值
- `GET /api/admin/videos` - 取得影片列表
- `POST /api/admin/videos/upload` - 上傳影片
- `DELETE /api/admin/videos/{filename}` - 刪除影片
- `PUT /api/admin/videos/current/{filename}` - 設定當前播放影片
- `GET /api/admin/videos/{filename}/info` - 取得影片詳細資訊

### ✅ 2. 前端管理系統

#### 後台管理頁面 (`frontend/admin.html`)
四大管理區塊:
1. **影片控制參數**
   - 速度設定(基礎/最大/最小)
   - 轉換時間、反向模式
   - 播放設定(循環/靜音/自動播放)
   - 快速預設按鈕

2. **距離偵測校準**
   - 距離範圍設定
   - 平滑處理參數
   - 啟動/停用延遲
   - 多人處理模式

3. **顯示模式控制**
   - 除錯模式開關
   - 展覽模式開關
   - 各項資訊顯示設定
   - 游標隱藏延遲

4. **影片管理**
   - 影片上傳(支援 MP4, WebM, OGG)
   - 影片列表顯示
   - 設定主影片
   - 刪除影片

#### 播放頁面 (`frontend/player.html`)
- **全螢幕影片播放**
- **即時距離偵測整合**
- **動態速度調整**
  - 平滑過渡(Ease-out 曲線)
  - 多人時選取最近者
  - 距離抖動過濾
  - 人臉遺失處理
- **除錯模式**
  - 顯示播放速度
  - 顯示偵測距離(含顏色警示)
  - 顯示人臉數量
  - 顯示 FPS
  - 顯示連線狀態
  - 顯示運行時間
- **展覽模式**
  - 全螢幕播放
  - 隱藏所有 UI
  - 自動隱藏游標
- **快捷鍵**
  - Ctrl+Shift+D: 切換除錯模式
  - Ctrl+Shift+E: 切換展覽模式

### ✅ 3. API 客戶端 (`frontend/js/api-client.js`)
- 封裝所有 REST API 呼叫
- WebSocket 連線管理
- 統一錯誤處理

### ✅ 4. 樣式系統
- **後台管理樣式** (`frontend/css/admin.css`)
  - 響應式設計
  - 側邊欄導航
  - 表單元件
  - 影片卡片
  
- **播放器樣式** (`frontend/css/player.css`)
  - 全螢幕支援
  - 除錯面板
  - 攝影機預覽
  - 動畫效果

## 專案結構

```
CalcDistanceYolo/
├── backend/
│   ├── main.py                      # ✅ 已更新路由
│   ├── app/
│   │   ├── api/
│   │   │   ├── admin_api.py        # ✅ 新增
│   │   │   ├── frontend.py
│   │   │   └── websocket.py
│   │   ├── models/
│   │   ├── services/
│   │   └── utils/
│   └── configs/
│       ├── project_config.json      # ✅ 新增
│       ├── sensor_config.json
│       └── network_config.json
├── frontend/
│   ├── admin.html                   # ✅ 新增
│   ├── player.html                  # ✅ 新增
│   ├── index.html                   # 原有監控頁面
│   ├── css/
│   │   ├── admin.css               # ✅ 新增
│   │   └── player.css              # ✅ 新增
│   ├── js/
│   │   └── api-client.js           # ✅ 新增
│   ├── videos/                      # ✅ 新增(影片存放)
│   └── cdn/
└── docs/
    └── projectDoc/
        └── DistanceVideo.md         # 規格文件
```

## 使用方式

### 1. 啟動服務

```powershell
cd backend
python main.py
```

服務將在 `http://localhost:8000` 啟動

### 2. 訪問介面

- **播放頁面**: http://localhost:8000/player.html
- **後台管理**: http://localhost:8000/admin.html
- **API 文件**: http://localhost:8000/docs

### 3. 基本流程

1. 開啟後台管理頁面
2. 在「影片管理」上傳影片(建議 WebM VP9 格式)
3. 設定為主影片
4. 調整「影片控制參數」和「距離偵測校準」
5. 開啟播放頁面測試
6. 使用快捷鍵切換模式

### 4. 建議配置

**正常展示**:
- baseSpeed: 1.0
- maxSpeed: 10.0
- minDistance: 50 cm
- maxDistance: 500 cm
- transitionTime: 500 ms

**快速反應**:
- baseSpeed: 2.0
- maxSpeed: 15.0
- transitionTime: 300 ms

**平滑體驗**:
- smoothingFactor: 0.3
- distanceThreshold: 10 cm
- activationDelay: 300 ms

## 技術特點

### 前端效能優化
- ✅ requestAnimationFrame 同步繪製
- ✅ GPU 加速(will-change, transform)
- ✅ 事件節流與防抖
- ✅ WebSocket 自動重連
- ✅ 記憶體管理(定時器清理)

### 距離控制演算法
- ✅ 線性插值計算速度
- ✅ Ease-out 平滑過渡
- ✅ 距離抖動過濾
- ✅ 多人自動選取最近者
- ✅ 無人臉逐步回復機制

### 使用者體驗
- ✅ 響應式設計
- ✅ 即時參數調整
- ✅ 視覺化狀態顯示
- ✅ 快捷鍵控制
- ✅ 全螢幕支援

## 下一步建議

1. **影片預覽功能**
   - 在後台管理顯示影片縮圖
   - 影片資訊讀取(時長、解析度)

2. **高級校準工具**
   - 即時距離曲線圖表
   - 速度響應曲線視覺化
   - A/B 測試模式

3. **資料記錄**
   - 觀眾互動記錄
   - 距離分佈統計
   - 使用時長分析

4. **多語言支援**
   - i18n 國際化
   - 語言切換功能

5. **效能監控**
   - 記憶體使用追蹤
   - FPS 穩定性分析
   - 8小時長時間測試

## 授權

© 2025 DistanceVideo Project

---

**建立日期**: 2025-01-09  
**版本**: v1.0.0  
**狀態**: ✅ 完整實作完成
