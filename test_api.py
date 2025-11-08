#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 Admin API
"""

import requests
import json

BASE_URL = "http://localhost:8000"

print("=== 測試 Admin API ===\n")

# 1. 測試取得配置
print("1️⃣ 測試 GET /api/admin/config")
try:
    response = requests.get(f"{BASE_URL}/api/admin/config")
    print(f"   狀態碼: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ 成功取得配置")
        print(f"   - baseSpeed: {data['data']['video']['baseSpeed']}")
        print(f"   - maxSpeed: {data['data']['video']['maxSpeed']}")
    else:
        print(f"   ❌ 失敗: {response.text}")
except Exception as e:
    print(f"   ❌ 錯誤: {e}")

print()

# 2. 測試更新配置
print("2️⃣ 測試 PUT /api/admin/config")
try:
    update_data = {
        "video": {
            "baseSpeed": 1.5,
            "maxSpeed": 12.0
        }
    }
    response = requests.put(
        f"{BASE_URL}/api/admin/config",
        json=update_data
    )
    print(f"   狀態碼: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ 成功更新配置")
        print(f"   - baseSpeed: {data['data']['video']['baseSpeed']}")
        print(f"   - maxSpeed: {data['data']['video']['maxSpeed']}")
    else:
        print(f"   ❌ 失敗: {response.text}")
except Exception as e:
    print(f"   ❌ 錯誤: {e}")

print()

# 3. 測試影片列表
print("3️⃣ 測試 GET /api/admin/videos")
try:
    response = requests.get(f"{BASE_URL}/api/admin/videos")
    print(f"   狀態碼: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ 成功取得影片列表")
        print(f"   - 影片數量: {len(data['data'])}")
    else:
        print(f"   ❌ 失敗: {response.text}")
except Exception as e:
    print(f"   ❌ 錯誤: {e}")

print()

# 4. 測試重置配置
print("4️⃣ 測試 POST /api/admin/config/reset")
try:
    response = requests.post(f"{BASE_URL}/api/admin/config/reset")
    print(f"   狀態碼: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ 成功重置配置")
        print(f"   - baseSpeed: {data['data']['video']['baseSpeed']}")
        print(f"   - maxSpeed: {data['data']['video']['maxSpeed']}")
    else:
        print(f"   ❌ 失敗: {response.text}")
except Exception as e:
    print(f"   ❌ 錯誤: {e}")

print("\n=== 測試完成 ===")
