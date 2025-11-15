#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
距離恢復機制測試腳本
用於驗證離開延遲與距離恢復功能
"""

import asyncio
import time
import json


async def test_recovery_logic():
    """
    模擬後端的恢復邏輯，驗證計算是否正確
    """
    print("=" * 60)
    print("距離恢復機制測試")
    print("=" * 60)
    
    # 配置參數
    deactivation_delay_ms = 1000  # 停止延遲 1 秒
    recovery_duration_ms = 3000   # 恢復持續 3 秒
    recovery_target_distance = 500  # 目標距離 500cm
    min_distance = 70  # 最小距離
    
    # 模擬場景
    scenarios = [
        {"time": 0.0, "distance": 80, "count": 1, "desc": "人在前方"},
        {"time": 0.5, "distance": 75, "count": 1, "desc": "人在前方"},
        {"time": 1.0, "distance": 0, "count": 0, "desc": "人離開！"},
        {"time": 1.5, "distance": 0, "count": 0, "desc": "延遲期"},
        {"time": 2.0, "distance": 0, "count": 0, "desc": "延遲期結束，開始恢復"},
        {"time": 2.5, "distance": 0, "count": 0, "desc": "恢復中 25%"},
        {"time": 3.0, "distance": 0, "count": 0, "desc": "恢復中 50%"},
        {"time": 3.5, "distance": 0, "count": 0, "desc": "恢復中 75%"},
        {"time": 4.0, "distance": 0, "count": 0, "desc": "恢復中 100%"},
        {"time": 5.0, "distance": 0, "count": 0, "desc": "恢復完成"},
    ]
    
    # 狀態變數
    last_detection_time = 0.0
    is_recovering = False
    recovery_start_time = 0.0
    recovery_start_distance = 0
    last_valid_distance = 0
    
    print("\n時間軸模擬：")
    print("-" * 60)
    print(f"{'時間(s)':<10} {'狀態':<15} {'輸出距離(cm)':<15} {'描述':<20}")
    print("-" * 60)
    
    for scenario in scenarios:
        current_time = scenario["time"]
        raw_distance = scenario["distance"]
        total_count = scenario["count"]
        desc = scenario["desc"]
        
        # 判斷是否有有效偵測
        has_valid_detection = total_count > 0 and raw_distance > 0
        
        # 計算輸出距離
        if has_valid_detection:
            # 有人偵測到
            last_detection_time = current_time
            last_valid_distance = raw_distance
            is_recovering = False
            output_distance = raw_distance
            status = "偵測中"
            
        else:
            # 沒有偵測到人
            time_since_last_detection = (current_time - last_detection_time) * 1000
            
            if time_since_last_detection < deactivation_delay_ms:
                # 延遲期間，保持最後距離
                output_distance = last_valid_distance
                status = "延遲期"
                
            else:
                # 開始恢復
                if not is_recovering:
                    is_recovering = True
                    recovery_start_time = current_time
                    recovery_start_distance = last_valid_distance if last_valid_distance > 0 else min_distance
                
                # 計算恢復進度
                recovery_elapsed = (current_time - recovery_start_time) * 1000
                recovery_progress = min(1.0, recovery_elapsed / recovery_duration_ms)
                
                # 套用 ease-out 緩動
                eased_progress = 1 - pow(1 - recovery_progress, 2)
                
                # 線性插值
                output_distance = recovery_start_distance + (recovery_target_distance - recovery_start_distance) * eased_progress
                
                status = f"恢復中 {int(recovery_progress * 100)}%"
        
        print(f"{current_time:<10.1f} {status:<15} {output_distance:<15.1f} {desc:<20}")
    
    print("-" * 60)
    print("\n✅ 測試完成！")
    print("\n預期行為：")
    print("1. 人在時，輸出真實距離（80cm, 75cm）")
    print("2. 人離開後，延遲 1 秒維持 75cm")
    print("3. 延遲結束後，3 秒內從 75cm 恢復到 500cm")
    print("4. 恢復過程使用 ease-out 緩動，視覺上更自然")
    print("\n" + "=" * 60)


async def test_api_endpoints():
    """
    測試 API 端點（需要伺服器運行）
    """
    try:
        import aiohttp
        
        print("\n" + "=" * 60)
        print("API 端點測試")
        print("=" * 60)
        
        base_url = "http://localhost:8000"
        
        async with aiohttp.ClientSession() as session:
            # 1. 取得當前配置
            print("\n1. 取得距離恢復機制配置...")
            async with session.get(f"{base_url}/api/distance-recovery-config") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ 成功: {json.dumps(data, indent=2, ensure_ascii=False)}")
                else:
                    print(f"❌ 失敗: HTTP {resp.status}")
            
            # 2. 更新配置
            print("\n2. 更新距離恢復機制配置...")
            new_config = {
                "enabled": True,
                "deactivation_delay_ms": 1500,
                "recovery_duration_ms": 2500,
                "recovery_target_distance": 500
            }
            async with session.put(
                f"{base_url}/api/distance-recovery-config",
                json=new_config
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ 成功: {json.dumps(data, indent=2, ensure_ascii=False)}")
                else:
                    print(f"❌ 失敗: HTTP {resp.status}")
            
            # 3. 驗證更新
            print("\n3. 驗證配置是否已更新...")
            async with session.get(f"{base_url}/api/distance-recovery-config") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ 成功: {json.dumps(data, indent=2, ensure_ascii=False)}")
                else:
                    print(f"❌ 失敗: HTTP {resp.status}")
        
        print("\n" + "=" * 60)
        print("✅ API 測試完成！")
        print("=" * 60)
        
    except ImportError:
        print("\n⚠ 需要安裝 aiohttp 才能測試 API：pip install aiohttp")
    except Exception as e:
        print(f"\n❌ API 測試失敗: {e}")
        print("請確認伺服器是否已啟動（python3.11 run.py）")


if __name__ == "__main__":
    print("\n開始測試距離恢復機制...\n")
    
    # 測試 1：邏輯驗證
    asyncio.run(test_recovery_logic())
    
    # 測試 2：API 端點測試（需要伺服器運行）
    print("\n是否要測試 API 端點？（需要伺服器運行）")
    print("提示：先執行 'python3.11 run.py' 啟動伺服器")
    choice = input("輸入 'y' 繼續，其他鍵跳過: ").lower().strip()
    
    if choice == 'y':
        asyncio.run(test_api_endpoints())
    else:
        print("\n已跳過 API 測試")
    
    print("\n測試結束！\n")
