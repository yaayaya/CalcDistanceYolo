# GPU 設定說明

## 支援的計算裝置

程式支援以下計算裝置:

### 1. **CPU** (所有平台)
- 所有電腦都支援
- 速度較慢,適合測試使用
- 設定值: `cpu`

### 2. **NVIDIA CUDA GPU** (Windows/Linux)
- 需要安裝 NVIDIA 顯示卡
- 需要安裝 CUDA 工具包
- 需要安裝支援 CUDA 的 PyTorch 版本
- 設定值: `cuda` 或 `cuda:0`, `cuda:1` (多 GPU 時)
- 速度最快,推薦用於生產環境

#### 安裝 CUDA 版本的 PyTorch:
```bash
# Windows/Linux with CUDA 11.8
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Windows/Linux with CUDA 12.1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### 3. **Apple Silicon MPS** (Mac M1/M2/M3)
- 僅支援 Apple Silicon (M1/M2/M3) Mac 電腦
- macOS 12.3 或更新版本
- 速度比 CPU 快很多
- 設定值: `mps`

#### Mac 安裝說明:
```bash
# Mac with Apple Silicon
pip install torch torchvision
```

## 如何使用

### 方法一: 在 GUI 中設定
1. 開啟程式
2. 切換到「參數設定」分頁
3. 在「計算裝置 (GPU/CPU)」區域選擇裝置
4. 點擊「💾 儲存所有設定」
5. 重新啟動偵測即可

### 方法二: 直接修改配置檔
編輯 `sensor_config.json`:
```json
{
  "model": {
    "device": "cuda"  // 或 "cpu", "mps", "cuda:0"
  }
}
```

## 效能比較

| 裝置類型 | 相對速度 | 適用場景 |
|---------|---------|---------|
| CPU | 1x (基準) | 測試、開發 |
| Apple MPS | 3-5x | Mac 使用者 |
| NVIDIA CUDA | 5-10x+ | 生產環境、高 FPS 需求 |

## 故障排除

### 問題 1: CUDA 不可用
**症狀**: 選擇 CUDA 後顯示「❌ CUDA 不可用」

**解決方案**:
1. 確認已安裝 NVIDIA 顯示卡驅動程式
2. 安裝支援 CUDA 的 PyTorch:
   ```bash
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```
3. 驗證安裝:
   ```bash
   python -c "import torch; print(torch.cuda.is_available())"
   ```

### 問題 2: MPS 不可用 (Mac)
**症狀**: Mac 電腦上選擇 MPS 後顯示不可用

**解決方案**:
1. 確認是 Apple Silicon (M1/M2/M3) Mac
2. 更新 macOS 到 12.3 或更新版本
3. 重新安裝 PyTorch:
   ```bash
   pip install --upgrade torch torchvision
   ```
4. 驗證安裝:
   ```bash
   python -c "import torch; print(torch.backends.mps.is_available())"
   ```

### 問題 3: GPU 記憶體不足
**症狀**: 使用 GPU 時出現 "CUDA out of memory" 錯誤

**解決方案**:
1. 降低影像尺寸 (從 640 改為 416 或 320)
2. 增加跳幀數 (vid_stride)
3. 降低攝影機解析度
4. 如有多個 GPU,選擇記憶體較大的:
   ```python
   # 在 Python 中查看 GPU 記憶體
   import torch
   for i in range(torch.cuda.device_count()):
       print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
       print(f"記憶體: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.2f} GB")
   ```

## 檢查當前裝置

執行以下指令檢查系統支援的裝置:

```python
import torch

print("CPU: 可用")
print(f"CUDA: {'可用' if torch.cuda.is_available() else '不可用'}")
if torch.cuda.is_available():
    for i in range(torch.cuda.device_count()):
        print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")

if hasattr(torch.backends, 'mps'):
    print(f"MPS: {'可用' if torch.backends.mps.is_available() else '不可用'}")
```

## 建議設定

### 開發/測試
- 裝置: CPU
- 影像尺寸: 416
- 跳幀數: 3

### Mac 使用者
- 裝置: mps
- 影像尺寸: 640
- 跳幀數: 2

### Windows/Linux with NVIDIA GPU
- 裝置: cuda
- 影像尺寸: 640
- 跳幀數: 1
- 解析度: 1920x1080
