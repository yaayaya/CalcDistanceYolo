# 🎨 FlurPaint 互動藝術裝置

基於 YOLO11 距離偵測的互動式藝術裝置,透過即時偵測觀眾距離,動態調整影像解析度,創造獨特的視覺互動體驗。

## ✨ 核心特色

- 🎯 **距離感應**: YOLO11 即時偵測人體距離
- 🌈 **動態解析度**: 距離越近越模糊,距離越遠越清晰
- 🚀 **即時串流**: WebSocket 1920x1080 影像串流
- ⚙️ **完全可調**: 所有參數可透過後台設定
- 💻 **設備選擇**: 支援 CPU / NVIDIA GPU / Apple GPU

## 🚀 快速開始

### 1. 啟動服務

```bash
# Windows
start_flur.bat

# 或手動啟動
cd backend
python main.py
```

### 2. 開啟頁面

- 🎨 展覽頁面: http://localhost:8000/flur
- 🎛️ 後台管理: http://localhost:8000/flur-admin
- 📊 監控後台: http://localhost:8000/admin

## 📚 文件

- [使用指南](docs/FlurPaint使用指南.md) - 完整使用說明
- [實作報告](docs/FlurPaint實作報告.md) - 技術實作細節
- [功能規格](docs/DistanceFlur.md) - 原始規格書

## ⚙️ 主要功能

### 視訊模糊控制
- 最小/最大解析度設定
- 加速/減速響應時間
- 移動閾值調整
- 啟動/停止延遲

### YOLO 設備選擇
- **CPU**: 相容性最佳 (預設)
- **CUDA**: NVIDIA GPU 加速
- **MPS**: Apple Silicon (M1/M2/M3)

### 顯示模式
- 除錯模式 (即時狀態資訊)
- 展覽模式 (全螢幕簡潔)
- 快捷鍵: `Ctrl+Shift+D` / `Ctrl+Shift+E`

## 🏗️ 技術架構

```
攝影機(1920x1080) → YOLO11 偵測 → WebSocket → Canvas 動態渲染
                         ↓              ↓
                     距離計算        Base64 編碼
                         ↓              ↓
                    解析度映射      平滑過渡顯示
```

## 📁 專案結構

```
CalcDistanceYolo/
├── backend/
│   ├── configs/
│   │   ├── project_config.json      # 視訊模糊控制、設備選擇
│   │   ├── sensor_config.json       # YOLO 參數、距離計算
│   │   └── network_config.json      # WebSocket 設定
│   ├── app/
│   │   ├── api/                     # API 端點
│   │   ├── services/                # 核心服務
│   │   └── utils/                   # 工具函式
│   └── main.py                      # FastAPI 主程式
├── frontend/
│   ├── flur.html                    # 展覽頁面
│   ├── flur_admin.html              # 後台管理
│   └── index.html                   # 監控後台
├── docs/                            # 說明文件
├── test_flur_system.py              # 系統測試
└── start_flur.bat                   # 快速啟動
```

## 🔌 API 端點

### WebSocket
- `/ws/flur` - 影像串流 (Base64 + 距離)
- `/ws/detection` - 完整偵測資料
- `/ws/live` - 簡化串流

### REST API
- `GET /api/project-config` - 取得配置
- `PUT /api/project-config` - 更新配置
- `POST /api/project-config/reset` - 重置配置

## 🎮 快捷鍵

**展覽頁面:**
- `Ctrl+Shift+D` - 切換除錯模式
- `Ctrl+Shift+E` - 切換展覽模式

## 📊 系統需求

- Python 3.8+
- OpenCV
- Ultralytics (YOLO11)
- FastAPI
- 攝影機 (USB 或內建)
- (選用) NVIDIA GPU + CUDA 或 Apple Silicon

## 🧪 測試

```bash
python test_flur_system.py
```

測試項目:
- ✅ 配置檔案載入
- ✅ API 端點連通
- ✅ 頁面訪問
- ✅ WebSocket 端點

## 📝 配置範例

**最小解析度**: 320px (最近距離)
**最大解析度**: 1920px (最遠距離)
**距離範圍**: 50-500 cm
**YOLO 設備**: CPU / CUDA / MPS

## 🎯 使用情境

### 藝術展覽
1. 全螢幕開啟展覽頁面
2. 觀眾靠近時影像模糊
3. 觀眾遠離時影像清晰
4. 創造互動式視覺體驗

### 調試測試
1. 開啟除錯模式
2. 查看即時距離和 FPS
3. 調整後台參數
4. 即時觀察效果變化

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request!

## 📄 授權

MIT License

## 🙏 致謝

- [Ultralytics YOLO](https://github.com/ultralytics/ultralytics)
- [FastAPI](https://fastapi.tiangolo.com/)
- [OpenCV](https://opencv.org/)

---

**專案版本**: 1.0.0  
**更新日期**: 2025-11-09  
**專案分支**: DistanceFlur

🎨 開始體驗互動藝術裝置吧!
