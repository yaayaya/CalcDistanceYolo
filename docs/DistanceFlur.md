# 🎨 互動藝術裝置 (FlurPaint) - 功能規格書

## 📋 專案概述

一個基於距離感應的互動式藝術裝置,透過 YOLO 偵測觀眾與攝影機的距離,動態調整前端影像解析度,創造獨特的視覺互動體驗。

### 核心概念

- **距離感應**: 使用 YOLO11 即時偵測人體距離
- **解析度變化**: 距離越近解析度越低,距離越遠解析度越高
- **即時通訊**: 透過 WebSocket 傳遞影像串流與距離資料
- **參數可調**: 所有控制參數可透過後台介面設定

---

## 🏗️ 系統架構

### 資料流程

```
攝影機 → 後端 YOLO 偵測 → WebSocket → 前端 Canvas 渲染
         ↓                    ↓
      距離計算              影像串流
         ↓                    ↓
    解析度映射            動態縮放顯示
```

### 技術實作原則

1. **後端**: 固定高解析度擷取影像 (1920x1080)
2. **前端**: 根據距離參數動態調整 Canvas 顯示解析度
3. **通訊**: WebSocket 即時推送距離與影像資料
4. **設定**: 參數儲存於 `project_config.json`

---

## ⚙️ 功能需求

### 1. 影像串流系統

#### 後端影像處理
- 固定以最高解析度 (1920x1080) 擷取攝影機畫面
- 避免硬體解析度切換造成的延遲與不穩定
- 同時執行 YOLO 人體偵測與距離計算
- 透過 WebSocket 推送影像幀與距離資料

#### 前端影像渲染
- 使用 Canvas 接收並顯示後端影像串流
- 根據距離參數動態調整 Canvas 渲染解析度
- 利用 GPU 硬體加速實現流暢縮放效果

---

### 2. 距離感應與解析度控制

#### 解析度映射規則

| 距離範圍 | 解析度變化 | 視覺效果 |
|---------|-----------|---------|
| 越近 | 越低 (最低 320x180) | 畫面模糊、像素化 |
| 中距離 | 漸進變化 | 平滑過渡 |
| 越遠 | 越高 (最高 1920x1080) | 畫面清晰、高解析度 |

#### 解析度約束
- **比例限制**: 固定 16:9 比例
- **寬度設定**: 可由後台設定寬度,高度自動計算 (height = width × 9 / 16)
- **最大解析度**: 1920x1080 (預設)
- **最小解析度**: 320x180 (預設)

#### 動態控制邏輯
```
距離資料 → 映射函數 (線性/非線性) → Canvas 縮放比例 → 即時渲染
```

---

### 3. 後台管理介面



#### 視訊模糊控制參數設定

| 參數名稱 | 說明 | 預設值 | 單位 | 備註 |
|---------|------|--------|------|------|
| **最小解析度** | 最近距離時的解析度寬度 | 320 | px | 高度自動計算 (16:9) |
| **最大解析度** | 最遠距離時的解析度寬度 | 1920 | px | 高度自動計算 (16:9) |
| **加速響應時間** | 解析度降低 (距離變近) 的過渡時間 | 500 | ms | 控制模糊化速度 |
| **減速響應時間** | 解析度提高 (距離變遠) 的過渡時間 | 1000 | ms | 控制清晰化速度 |
| **移動閾值** | 觸發解析度變化的最小距離變化量 | 10 | cm | 避免微小抖動 |
| **啟動延遲** | 偵測到人體後延遲啟動的時間 | 200 | ms | 防止誤觸發 |
| **停止延遲** | 人體離開後延遲停止的時間 | 500 | ms | 平滑退場效果 |
| **取樣頻率** | 距離資料取樣與更新頻率 | 30 | fps | 影響響應靈敏度 |

#### 設定儲存
- 所有參數變更自動儲存至 `project_config.json`
- 支援即時套用變更 (無需重啟)
- 提供「重置為預設值」功能

---

## 🔧 技術實作細節

### 後端固定高解析度擷取方案

**優點:**
- ✅ 避免攝影機硬體切換解析度的延遲
- ✅ 保持影像品質穩定性
- ✅ 簡化攝影機控制邏輯
- ✅ 支援前端自由縮放

**實作:**
```python
# 後端固定擷取 1920x1080
camera_config = {
    "width": 1920,
    "height": 1080,
    "fps": 30
}
```

---

### 前端 Canvas 動態縮放方案


- **除錯模式 (Debug Mode)**：

- **展覽模式 (Exhibition Mode)**：
  - 全螢幕影片播放
  - 隱藏所有狀態資訊和 UI 元素
  - 提供切換模式的隱藏熱鍵 (如：Ctrl+Shift+D)

**優點:**
- ✅ 即時快速響應距離變化
- ✅ GPU 硬體加速,效能優異
- ✅ 平滑過渡無卡頓
- ✅ 靈活的視覺效果控制

**實作邏輯:**
```javascript
// 距離 → 解析度映射函數 (線性)
function mapDistanceToResolution(distance, minDist, maxDist, minRes, maxRes) {
    const ratio = Math.min(1, Math.max(0, 
        (distance - minDist) / (maxDist - minDist)
    ));
    const width = Math.round(minRes + ratio * (maxRes - minRes));
    const height = Math.round(width * 9 / 16);  // 固定 16:9
    return { width, height };
}

// Canvas 動態縮放渲染
canvas.width = targetResolution.width;
canvas.height = targetResolution.height;
ctx.drawImage(videoFrame, 0, 0, canvas.width, canvas.height);
```

---

### 距離資料與解析度快速反應

**WebSocket 資料格式:**
```json
{
    "type": "frame_data",
    "image": "base64_encoded_image",
    "distance": 185.3,
    "timestamp": 1699459200.123,
    "resolution": {
        "current": { "width": 1280, "height": 720 },
        "target": { "width": 960, "height": 540 }
    }
}
```

**前端接收處理:**
1. 即時接收距離與影像資料
2. 計算目標解析度
3. 平滑過渡至目標解析度 (CSS transition 或 GSAP)
4. 更新 Canvas 渲染

---

### 穩定性優化機制

#### 節流 (Throttle)
```javascript
// 限制解析度更新頻率,避免過度頻繁變化
const throttledUpdateResolution = throttle(updateResolution, 100); // 100ms
```

#### 防抖 (Debounce)
```javascript
// 距離穩定後才變更解析度,避免抖動
const debouncedUpdateResolution = debounce(updateResolution, 300); // 300ms
```

#### 移動閾值
```javascript
// 只有距離變化超過閾值才觸發更新
if (Math.abs(newDistance - currentDistance) > threshold) {
    updateResolution(newDistance);
}
```


---

## 🚀 開發注意事項

### ⚠️ 重要提醒

1. **單一攝影機來源**: 後端統一管理攝影機,前端接收串流畫面
2. **不切換硬體解析度**: 避免攝影機硬體切換造成卡頓
3. **參數持久化**: 所有後台設定儲存至 `project_config.json`
4. **不需要測試檔案**: 整合至主程式,無需額外 `test.py`
5. **16:9 比例鎖定**: 寬度可調,高度自動計算


---

## 📝 開發檢查清單

- [ ] 後端固定 1920x1080 擷取影像
- [ ] 實作 YOLO 距離偵測服務
- [ ] 建立 WebSocket 影像串流端點
- [ ] 實作距離→解析度映射函數
- [ ] 前端 Canvas 動態渲染
- [ ] 後台管理介面 (參數設定)
- [ ] `project_config.json` 讀寫功能
- [ ] 參數即時套用 (無需重啟)
- [ ] 節流/防抖穩定性優化
- [ ] 16:9 比例自動計算

---

## 💡 進階功能建議 (可選)

### 非線性映射曲線
```javascript
// 使用 easing function 創造更自然的過渡
function easeOutQuad(t) {
    return t * (2 - t);
}

function mapDistanceWithEasing(distance, minDist, maxDist, minRes, maxRes) {
    const ratio = (distance - minDist) / (maxDist - minDist);
    const easedRatio = easeOutQuad(ratio);
    return minRes + easedRatio * (maxRes - minRes);
}
```

### 多人追蹤模式
- 偵測多人時取最近距離
- 或取平均距離
- 可於後台設定模式

### 距離歷史記錄
- 記錄距離變化曲線
- 提供數據分析與視覺化
- 用於展覽期間的觀眾行為分析

---

**文件版本**: 1.0  
**最後更新**: 2025-11-09  
**專案分支**: DistanceFlur  
**相關文件**: 
- [專案結構](./專案結構.md)
- [快速啟動](./快速啟動.md)
- [原始 README](./原始README.md)