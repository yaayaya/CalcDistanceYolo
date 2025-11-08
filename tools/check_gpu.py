#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU/裝置檢測工具
檢查系統支援哪些計算裝置 (CPU, CUDA, MPS)
"""

def check_devices():
    """檢查可用的計算裝置"""
    print("=" * 60)
    print("計算裝置檢測報告")
    print("=" * 60)
    
    # 檢查 PyTorch
    try:
        import torch
        print(f"✓ PyTorch 版本: {torch.__version__}")
    except ImportError:
        print("❌ PyTorch 未安裝")
        print("\n安裝指令:")
        print("  pip install torch torchvision")
        return
    
    print()
    
    # 檢查 CPU
    print("【CPU】")
    print("  狀態: ✓ 可用")
    print("  說明: 所有系統都支援")
    print()
    
    # 檢查 CUDA
    print("【NVIDIA CUDA GPU】")
    if torch.cuda.is_available():
        print(f"  狀態: ✓ 可用")
        print(f"  CUDA 版本: {torch.version.cuda}")
        print(f"  GPU 數量: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(i)
            print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
            print(f"    - 記憶體: {props.total_memory / 1024**3:.2f} GB")
            print(f"    - 計算能力: {props.major}.{props.minor}")
    else:
        print("  狀態: ❌ 不可用")
        print("  說明: 需要 NVIDIA 顯示卡和 CUDA 工具包")
        print("  安裝指令:")
        print("    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118")
    print()
    
    # 檢查 MPS (Apple Silicon)
    print("【Apple Silicon MPS】")
    if hasattr(torch.backends, 'mps'):
        if torch.backends.mps.is_available():
            print("  狀態: ✓ 可用")
            print("  說明: Apple M1/M2/M3 GPU 加速")
            if torch.backends.mps.is_built():
                print("  MPS 後端: 已編譯")
        else:
            print("  狀態: ❌ 不可用")
            print("  說明: 需要 Apple Silicon Mac 和 macOS 12.3+")
    else:
        print("  狀態: ❌ 不支援")
        print("  說明: PyTorch 版本過舊或非 Mac 系統")
    print()
    
    # 建議
    print("=" * 60)
    print("建議使用的裝置:")
    print("=" * 60)
    
    if torch.cuda.is_available():
        print("✓ 推薦使用: cuda (NVIDIA GPU)")
        print("  - 最快的推理速度")
        print("  - 在 GUI 中選擇 'cuda'")
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        print("✓ 推薦使用: mps (Apple Silicon)")
        print("  - Mac 專用 GPU 加速")
        print("  - 在 GUI 中選擇 'mps'")
    else:
        print("✓ 使用: cpu")
        print("  - 速度較慢,但所有系統都支援")
        print("  - 建議安裝 GPU 支援以提升效能")
    
    print()
    print("=" * 60)
    
    # 效能測試
    print("\n是否要進行簡單的效能測試? (y/n): ", end="")
    try:
        choice = input().lower()
        if choice == 'y':
            performance_test()
    except:
        pass


def performance_test():
    """簡單的效能測試"""
    import torch
    import time
    
    print("\n" + "=" * 60)
    print("效能測試 (矩陣運算)")
    print("=" * 60)
    
    size = 5000
    iterations = 10
    
    devices_to_test = ["cpu"]
    if torch.cuda.is_available():
        devices_to_test.append("cuda")
    if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        devices_to_test.append("mps")
    
    for device in devices_to_test:
        print(f"\n測試裝置: {device}")
        
        try:
            # 建立測試資料
            a = torch.randn(size, size, device=device)
            b = torch.randn(size, size, device=device)
            
            # 熱身
            _ = torch.matmul(a, b)
            if device != "cpu":
                torch.cuda.synchronize() if device == "cuda" else None
            
            # 測試
            start = time.time()
            for _ in range(iterations):
                c = torch.matmul(a, b)
                if device == "cuda":
                    torch.cuda.synchronize()
            elapsed = time.time() - start
            
            print(f"  完成 {iterations} 次 {size}x{size} 矩陣乘法")
            print(f"  總耗時: {elapsed:.3f} 秒")
            print(f"  平均: {elapsed/iterations*1000:.1f} ms/次")
            
        except Exception as e:
            print(f"  ❌ 測試失敗: {e}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    check_devices()
