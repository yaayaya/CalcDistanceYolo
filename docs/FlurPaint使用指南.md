# 🎨 FlurPaint 互動藝術裝置 - 使用指南

## 📋 功能概述

FlurPaint 是一個基於 YOLO11 距離偵測的互動藝術裝置,透過即時偵測觀眾與攝影機的距離,動態調整前端影像解析度,創造獨特的視覺互動體驗。

### 核心特色

- **距離感應**: 使用 YOLO11 即時偵測人體距離
- **解析度變化**: 距離越近解析度越低(模糊),距離越遠解析度越高(清晰)
- **即時串流**: 透過 WebSocket 傳遞 1920x1080 影像串流與距離資料
- **參數可調**: 所有控制參數可透過後台介面設定
- **設備選擇**: 支援 CPU / NVIDIA GPU (CUDA) / Apple Silicon GPU (MPS) 推論

---

## 🚀 快速啟動

### 1. 啟動後端服務

```powershell
cd backend
python main.py
```

服務啟動後會在 http://localhost:8000 運行

### 2. 開啟頁面

- **展覽頁面**: http://localhost:8000/flur
- **後台管理**: http://localhost:8000/flur-admin
- **監控後台**: http://localhost:8000/admin
- **API 文件**: http://localhost:8000/docs

---

## 🎛️ 後台管理介面

訪問 http://localhost:8000/flur-admin 可以設定以下參數:

### 視訊模糊控制參數

| 參數 | 說明 | 預設值 |
|------|------|--------|
| 最小解析度寬度 | 最近距離時的解析度 | 320 px |
| 最大解析度寬度 | 最遠距離時的解析度 | 1920 px |
| 加速響應時間 | 模糊化過渡時間 | 500 ms |
| 減速響應時間 | 清晰化過渡時間 | 1000 ms |
| 移動閾值 | 觸發變化的最小距離變化 | 10 cm |
| 啟動延遲 | 偵測到人後延遲啟動 | 200 ms |
| 停止延遲 | 人離開後延遲停止 | 500 ms |
| 取樣頻率 | 距離資料更新頻率 | 30 fps |

### 距離映射設定

- **最小距離**: 對應最低解析度的距離 (預設 50 cm)
- **最大距離**: 對應最高解析度的距離 (預設 500 cm)
- **緩動函數**: 映射曲線 (線性/緩入/緩出/緩入緩出)

### YOLO 推論設備

- **CPU**: 適用於所有電腦,相容性最佳
- **CUDA**: NVIDIA GPU 加速,需要安裝 CUDA
- **MPS**: Apple Silicon (M1/M2/M3) GPU 加速

### 顯示模式

- **除錯模式**: 顯示即時狀態資訊 (距離、FPS、解析度等)
- **展覽模式**: 全螢幕簡潔顯示,只顯示影像
- **顯示 FPS**: 是否顯示幀率
- **顯示距離**: 是否顯示距離資訊

---

## ⌨️ 快捷鍵

在展覽頁面 (flur.html) 中:

- **Ctrl+Shift+D**: 切換除錯模式
- **Ctrl+Shift+E**: 切換展覽模式

---

## 🔧 技術架構

### 後端

- **固定解析度擷取**: 攝影機固定以 1920x1080 擷取影像
- **YOLO11 偵測**: 即時偵測人體並計算距離
- **Base64 編碼**: 影像編碼為 JPEG 後透過 WebSocket 傳輸
- **WebSocket 串流**: `/ws/flur` 端點推送影像與距離資料

### 前端

- **Canvas 渲染**: 接收 Base64 影像並動態調整解析度
- **平滑過渡**: 使用 Lerp 實現解析度平滑變化
- **16:9 比例鎖定**: 寬度可調,高度自動計算

### 資料流程

```
攝影機 → 後端 YOLO 偵測 → WebSocket → 前端 Canvas 渲染
         ↓                    ↓
      距離計算              影像串流
         ↓                    ↓
    解析度映射            動態縮放顯示
```

---

## 📁 檔案結構

```
backend/
├── configs/
│   ├── project_config.json       # 專案配置 (視訊模糊控制、YOLO設備)
│   ├── sensor_config.json        # 感測器配置 (YOLO參數、距離計算)
│   └── network_config.json       # 網路配置 (WebSocket設定)
├── app/
│   ├── api/
│   │   ├── websocket.py          # WebSocket 端點 (/ws/flur)
│   │   └── frontend.py           # REST API (/api/project-config)
│   ├── services/
│   │   ├── detector.py           # YOLO 偵測服務 (含 Base64 編碼)
│   │   └── calculator.py         # 距離計算器
│   └── utils/
│       └── config_loader.py      # 配置載入器
└── main.py                       # FastAPI 主程式

frontend/
├── flur.html                     # 展覽頁面 (Canvas 動態渲染)
├── flur_admin.html               # 後台管理頁面
├── index.html                    # 原監控後台
├── script.js                     # 原後台腳本
└── style.css                     # 原後台樣式
```

---

## 🔌 API 端點

### WebSocket

- **`/ws/flur`**: FlurPaint 影像串流 (Base64 JPEG + 距離資料)
- **`/ws/detection`**: 完整偵測資料 (bbox, confidence, fps 等)
- **`/ws/live`**: 簡化版串流 (只有距離和人數)

### REST API

- **`GET /api/project-config`**: 取得專案配置
- **`PUT /api/project-config`**: 更新專案配置
- **`POST /api/project-config/reset`**: 重置為預設值
- **`GET /api/network-config`**: 取得網路配置
- **`POST /api/detector/refresh`**: 重新載入配置

---

## 📊 WebSocket 資料格式

### `/ws/flur` 回傳格式

```json
{
  "type": "frame_data",
  "image": "base64_encoded_jpeg_string",
  "distance": 185.3,
  "total_count": 2,
  "timestamp": 1699459200.123,
  "resolution": {
    "source": {
      "width": 1920,
      "height": 1080
    }
  }
}
```

---

## 🎯 使用情境

### 展覽模式

1. 開啟 http://localhost:8000/flur
2. 設定為全螢幕 (F11)
3. 觀眾靠近時影像變模糊,遠離時變清晰

### 除錯模式

1. 按 Ctrl+Shift+D 開啟除錯覆蓋層
2. 查看即時距離、FPS、解析度等資訊
3. 用於調整參數和測試效果

### 後台調整

1. 開啟 http://localhost:8000/flur-admin
2. 調整視訊模糊控制參數
3. 切換 YOLO 推論設備 (CPU/GPU)
4. 儲存設定後即時生效

---

## ⚠️ 注意事項

1. **攝影機解析度**: 後端固定以 1920x1080 擷取,不會切換硬體解析度
2. **設備選擇**:
   - CPU: 所有電腦都可用,速度較慢
   - CUDA: 需要 NVIDIA 顯示卡且已安裝 CUDA
   - MPS: 需要 M1/M2/M3 Mac 且 PyTorch 2.0+
3. **配置檔案**: project_config.json 會在首次啟動時自動建立
4. **即時套用**: 修改配置後會立即重新載入偵測器

---

## 🐛 故障排除

### WebSocket 連線失敗

- 確認後端服務已啟動
- 檢查防火牆設定
- 查看瀏覽器主控台錯誤訊息

### 影像不顯示

- 確認攝影機已正確連接
- 檢查 sensor_config.json 中的 camera.source 設定
- 查看後端終端機錯誤訊息

### GPU 不可用

- CUDA: 執行 `python tools/check_gpu.py` 檢查
- MPS: 確認 PyTorch 版本 >= 2.0
- 若無法使用 GPU,可切換為 CPU

---

## 📝 版本資訊

- **版本**: 1.0.0
- **更新日期**: 2025-11-09
- **專案分支**: DistanceFlur
- **相關文件**: [DistanceFlur.md](docs/DistanceFlur.md)

---

## 🎉 開始體驗

現在就啟動服務,訪問 http://localhost:8000/flur 開始體驗互動藝術裝置吧!
