# FPS 優化總結

## 🎯 已完成的優化

### 1. 前端 FPS 顯示修正
**問題：**
- 使用混合的時間函數（`Date.now()` 和 `performance.now()`）
- 過度的節流限制（16ms）阻止了正常渲染
- FPS 計算邏輯錯誤

**解決方案：**
```javascript
// 修正前
let lastFpsUpdate = Date.now();  // ❌ 不一致
if (now - lastFrameTime < 16) return;  // ❌ 過度限制

// 修正後
let lastFpsUpdate = performance.now();  // ✅ 統一使用高精度時間
// 移除節流限制，讓幀數正常顯示  // ✅ 正常渲染
```

### 2. 後端 JPEG 編碼優化
**問題：**
- 使用預設編碼參數，速度較慢
- JPEG 品質設定為 100（過高）

**解決方案：**
```python
# 優化編碼參數
encode_param = [
    int(cv2.IMWRITE_JPEG_QUALITY), quality,
    int(cv2.IMWRITE_JPEG_OPTIMIZE), 0,      # 關閉優化以加速
    int(cv2.IMWRITE_JPEG_PROGRESSIVE), 0    # 關閉漸進式以加速
]
```

### 3. 配置參數調整

#### sensor_config.json
```json
{
  "vid_stride": 2,              // 4 → 2 (提高偵測頻率)
  "target_fps": 30,
  "use_fps_limit": false        // true → false (移除限制)
}
```

#### project_config.json
```json
{
  "sample_rate": 20,            // 15 → 20 (提高取樣率)
  "jpeg_quality": 75,           // 100 → 75 (降低品質提速)
  "max_fps": 30                 // 10 → 30 (提高目標)
}
```

## 📊 預期效果

| 項目 | 優化前 | 優化後 | 改善 |
|-----|--------|--------|------|
| JPEG 編碼 | ~50ms | ~20ms | ⬆️ 60% |
| 前端限制 | 受限 16ms | 無限制 | ⬆️ 無上限 |
| 品質設定 | 100 | 75 | ⬆️ 30% 速度 |
| FPS 顯示 | 不正確 | ✅ 正確 | - |
| vid_stride | 4 幀 | 2 幀 | ⬆️ 2x 頻率 |

## 🔧 測試方法

### 1. 使用測試頁面
開啟：`http://localhost:8000/test_fps_display.html`

這個簡化頁面只顯示 FPS 和統計資訊，方便快速測試。

### 2. 使用主頁面
開啟：`http://localhost:8000/flur.html`

開啟除錯模式（`Ctrl+Shift+D`）查看詳細 FPS 資訊。

### 3. 監控後端效能
```bash
# 查看 Python 進程 CPU 使用率
top -pid $(pgrep -f "python.*run.py")

# 或使用 htop
htop -p $(pgrep -f "python.*run.py")
```

## 🎯 進一步優化建議

### 如果 FPS 仍然低於預期：

1. **降低解析度範圍**
   ```json
   "min_resolution_width": 160,    // 100 → 160
   "max_resolution_width": 1280    // 1920 → 1280
   ```

2. **降低 JPEG 品質**
   ```json
   "jpeg_quality": 60,             // 75 → 60
   "max_jpeg_quality": 60          // 75 → 60
   ```

3. **增加跳幀**
   ```json
   "vid_stride": 3                 // 2 → 3
   ```

4. **降低圖像尺寸**
   ```json
   "imgsz": 320                    // 416 → 320
   ```

5. **關閉模糊效果**
   ```json
   "canvas_filter": { "enabled": false },
   "blur_overlay": { "enabled": false }
   ```

## 🐛 故障排除

### 問題：FPS 顯示為 0 或不更新
**檢查：**
- WebSocket 是否成功連線
- 後端是否正常運行
- 瀏覽器控制台是否有錯誤

### 問題：FPS 顯示但很低（<10）
**可能原因：**
- YOLO 推論速度慢（檢查 GPU 是否啟用）
- 網路延遲（檢查 WebSocket 延遲）
- 影像編碼慢（降低品質/解析度）

### 問題：畫面卡頓但 FPS 顯示正常
**可能原因：**
- 前端渲染瓶頸（關閉模糊效果）
- Canvas 尺寸過大（降低最大解析度）

## 📝 效能分析工具

### Chrome DevTools
1. F12 開啟開發者工具
2. Performance 標籤
3. 錄製 5-10 秒
4. 分析幀渲染時間

### Network 面板
查看 WebSocket 訊息大小和頻率

## ✅ 驗證清單

- [ ] FPS 正確顯示在除錯面板
- [ ] FPS 達到目標值（15-30）
- [ ] 畫面流暢無卡頓
- [ ] 距離變化時平滑過渡
- [ ] CPU 使用率合理（<80%）
- [ ] WebSocket 連線穩定

## 🎉 完成！

如果以上優化仍無法達到理想 FPS，可能需要：
1. 升級硬體（更快的 CPU/GPU）
2. 使用更小的 YOLO 模型（yolo11n → yolo11-tiny）
3. 降低攝影機解析度
4. 考慮使用硬體編碼器
