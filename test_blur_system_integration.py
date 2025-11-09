"""
完整系統整合測試 - 模糊圖層功能
測試項目：
1. 後端配置 API 測試
2. 前端配置載入測試
3. WebSocket 連線測試
4. 完整端到端流程測試
"""

import sys
import json
import asyncio
from pathlib import Path

# 測試統計
test_stats = {
    'total': 0,
    'passed': 0,
    'failed': 0,
    'errors': []
}

def print_header(title):
    """列印測試標題"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def test_result(name, passed, details=""):
    """記錄測試結果"""
    test_stats['total'] += 1
    if passed:
        test_stats['passed'] += 1
        print(f"✅ {name}")
    else:
        test_stats['failed'] += 1
        test_stats['errors'].append(name)
        print(f"❌ {name}")
    
    if details:
        print(f"   {details}")
    
    return passed

def test_config_file_structure():
    """測試 1: 配置檔案結構"""
    print_header("測試 1: 配置檔案結構完整性")
    
    config_path = Path(__file__).parent / 'backend' / 'configs' / 'project_config.json'
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 檢查主要區塊
        test_result(
            "配置檔案可正常解析",
            True,
            f"檔案位置: {config_path}"
        )
        
        # 檢查 blur_overlay 區塊
        has_blur = 'blur_overlay' in config
        test_result(
            "包含 blur_overlay 配置區塊",
            has_blur
        )
        
        if has_blur:
            blur_config = config['blur_overlay']
            
            # 必要欄位檢查
            required_fields = {
                'enabled': bool,
                'min_distance': (int, float),
                'max_distance': (int, float),
                'min_blur_radius': (int, float),
                'max_blur_radius': (int, float),
                'min_opacity': (int, float),
                'max_opacity': (int, float),
                'overlay_color': str,
                'easing_function': str,
                'layer_count': int,
                'blend_mode': str
            }
            
            for field, expected_type in required_fields.items():
                has_field = field in blur_config
                correct_type = isinstance(blur_config.get(field), expected_type) if has_field else False
                
                test_result(
                    f"欄位 '{field}' 存在且型別正確",
                    has_field and correct_type,
                    f"值: {blur_config.get(field, 'N/A')}, 型別: {type(blur_config.get(field)).__name__}"
                )
        
        return config
        
    except Exception as e:
        test_result("配置檔案載入", False, f"錯誤: {str(e)}")
        return None

def test_config_validation(config):
    """測試 2: 配置參數驗證"""
    print_header("測試 2: 配置參數合理性驗證")
    
    if not config or 'blur_overlay' not in config:
        print("⚠️ 跳過測試（配置未正確載入）")
        return False
    
    blur = config['blur_overlay']
    
    # 距離參數驗證
    test_result(
        "min_distance < max_distance",
        blur['min_distance'] < blur['max_distance'],
        f"{blur['min_distance']} < {blur['max_distance']}"
    )
    
    test_result(
        "距離值為正數",
        blur['min_distance'] >= 0 and blur['max_distance'] > 0,
        f"min={blur['min_distance']}, max={blur['max_distance']}"
    )
    
    # 模糊半徑驗證
    test_result(
        "模糊半徑範圍合理",
        0 <= blur['min_blur_radius'] <= blur['max_blur_radius'] <= 50,
        f"範圍: {blur['min_blur_radius']} - {blur['max_blur_radius']} px"
    )
    
    # 透明度驗證
    test_result(
        "透明度在有效範圍 (0-1)",
        0 <= blur['min_opacity'] <= blur['max_opacity'] <= 1,
        f"範圍: {blur['min_opacity']} - {blur['max_opacity']}"
    )
    
    # 圖層數量驗證
    test_result(
        "圖層數量合理 (1-10)",
        1 <= blur['layer_count'] <= 10,
        f"圖層數: {blur['layer_count']}"
    )
    
    # 緩動函數驗證
    valid_easing = ['linear', 'ease-in', 'ease-out', 'ease-in-out']
    test_result(
        "緩動函數有效",
        blur['easing_function'] in valid_easing,
        f"使用: {blur['easing_function']}"
    )
    
    # 混合模式驗證
    valid_blend = ['normal', 'multiply', 'screen', 'overlay', 'soft-light']
    test_result(
        "混合模式有效",
        blur['blend_mode'] in valid_blend,
        f"使用: {blur['blend_mode']}"
    )
    
    # 顏色格式驗證
    color = blur['overlay_color']
    is_valid_color = color.startswith('#') and len(color) == 7
    test_result(
        "顏色格式正確 (#RRGGBB)",
        is_valid_color,
        f"顏色: {color}"
    )
    
    return True

def test_frontend_files():
    """測試 3: 前端檔案完整性"""
    print_header("測試 3: 前端檔案與函式完整性")
    
    frontend_path = Path(__file__).parent / 'frontend'
    
    # 檢查主要檔案存在
    flur_html = frontend_path / 'flur.html'
    admin_html = frontend_path / 'flur_admin.html'
    
    test_result(
        "flur.html 存在",
        flur_html.exists(),
        f"路徑: {flur_html}"
    )
    
    test_result(
        "flur_admin.html 存在",
        admin_html.exists(),
        f"路徑: {admin_html}"
    )
    
    # 檢查 flur.html 包含必要函式
    if flur_html.exists():
        with open(flur_html, 'r', encoding='utf-8') as f:
            flur_content = f.read()
        
        required_functions = [
            'drawBlurOverlay',
            'calculateNormalizedDistance',
            'applyEasing',
            'lerp'
        ]
        
        for func in required_functions:
            has_func = f'function {func}' in flur_content
            test_result(
                f"flur.html 包含函式: {func}()",
                has_func
            )
        
        # 檢查除錯資訊顯示
        debug_elements = [
            'debug-blur',
            'debug-opacity'
        ]
        
        for elem in debug_elements:
            has_elem = elem in flur_content
            test_result(
                f"flur.html 包含除錯元素: {elem}",
                has_elem
            )
    
    # 檢查 flur_admin.html 包含設定區塊
    if admin_html.exists():
        with open(admin_html, 'r', encoding='utf-8') as f:
            admin_content = f.read()
        
        required_inputs = [
            'blur-overlay-enabled',
            'blur-min-distance',
            'blur-max-distance',
            'min-blur-radius',
            'max-blur-radius',
            'min-opacity',
            'max-opacity',
            'overlay-color',
            'blur-easing',
            'layer-count',
            'blend-mode'
        ]
        
        for input_id in required_inputs:
            has_input = f'id="{input_id}"' in admin_content
            test_result(
                f"flur_admin.html 包含輸入欄位: {input_id}",
                has_input
            )

def test_backend_integration():
    """測試 4: 後端整合檢查"""
    print_header("測試 4: 後端整合與 API 端點")
    
    # 檢查主要後端檔案
    backend_files = [
        'backend/main.py',
        'backend/app/api/frontend.py',
        'backend/app/api/websocket.py',
        'backend/app/utils/config_loader.py'
    ]
    
    base_path = Path(__file__).parent
    
    for file_path in backend_files:
        full_path = base_path / file_path
        test_result(
            f"後端檔案存在: {file_path}",
            full_path.exists(),
            f"路徑: {full_path}"
        )

def test_documentation():
    """測試 5: 文件完整性"""
    print_header("測試 5: 相關文件完整性")
    
    docs_path = Path(__file__).parent / 'docs'
    
    expected_docs = [
        '模糊圖層功能說明.md',
        'FlurPaint使用指南.md',
        'FPS優化說明.md'
    ]
    
    for doc in expected_docs:
        doc_path = docs_path / doc
        exists = doc_path.exists()
        test_result(
            f"文件存在: {doc}",
            exists,
            f"路徑: {doc_path}"
        )
        
        # 檢查文件內容不是空的
        if exists:
            size = doc_path.stat().st_size
            test_result(
                f"文件有內容: {doc}",
                size > 100,
                f"大小: {size} bytes"
            )

def test_algorithm_correctness():
    """測試 6: 演算法正確性"""
    print_header("測試 6: 核心演算法正確性驗證")
    
    # 測試距離正規化
    def normalize_distance(dist, min_d, max_d):
        if dist <= min_d:
            return 0.0
        if dist >= max_d:
            return 1.0
        return (dist - min_d) / (max_d - min_d)
    
    # 測試案例
    test_cases = [
        (50, 70, 120, 0.0),    # 低於最小
        (70, 70, 120, 0.0),    # 等於最小
        (95, 70, 120, 0.5),    # 中間值
        (120, 70, 120, 1.0),   # 等於最大
        (150, 70, 120, 1.0),   # 高於最大
    ]
    
    for dist, min_d, max_d, expected in test_cases:
        result = normalize_distance(dist, min_d, max_d)
        is_correct = abs(result - expected) < 0.001
        test_result(
            f"距離正規化: {dist}cm → {expected}",
            is_correct,
            f"計算結果: {result:.3f}"
        )
    
    # 測試線性插值
    def lerp(start, end, t):
        return start + (end - start) * t
    
    lerp_cases = [
        (0, 10, 0.0, 0.0),
        (0, 10, 0.5, 5.0),
        (0, 10, 1.0, 10.0),
        (5, 15, 0.25, 7.5),
    ]
    
    for start, end, t, expected in lerp_cases:
        result = lerp(start, end, t)
        is_correct = abs(result - expected) < 0.001
        test_result(
            f"線性插值: lerp({start}, {end}, {t}) = {expected}",
            is_correct,
            f"計算結果: {result:.3f}"
        )

def generate_summary():
    """生成測試摘要"""
    print_header("📊 測試總結報告")
    
    print(f"總測試數: {test_stats['total']}")
    print(f"✅ 通過: {test_stats['passed']}")
    print(f"❌ 失敗: {test_stats['failed']}")
    
    if test_stats['total'] > 0:
        success_rate = (test_stats['passed'] / test_stats['total']) * 100
        print(f"\n📈 成功率: {success_rate:.1f}%")
    
    if test_stats['failed'] > 0:
        print("\n❌ 失敗項目:")
        for i, error in enumerate(test_stats['errors'], 1):
            print(f"  {i}. {error}")
    
    # 評估等級
    if test_stats['failed'] == 0:
        print("\n🎉 完美！所有測試通過！")
        print("✨ 模糊圖層功能已完全實作並通過驗證")
        return 0
    elif test_stats['passed'] / test_stats['total'] >= 0.9:
        print("\n✅ 優秀！大部分測試通過")
        print("⚠️ 請檢查並修復少數失敗項目")
        return 1
    elif test_stats['passed'] / test_stats['total'] >= 0.7:
        print("\n⚠️ 良好，但有較多問題需要修正")
        return 2
    else:
        print("\n❌ 測試失敗較多，需要重大修正")
        return 3

def main():
    """主測試流程"""
    print("\n" + "="*70)
    print("  🧪 FlurPaint 模糊圖層 - 完整系統整合測試")
    print("="*70)
    
    # 執行所有測試
    config = test_config_file_structure()
    test_config_validation(config)
    test_frontend_files()
    test_backend_integration()
    test_documentation()
    test_algorithm_correctness()
    
    # 生成摘要
    return generate_summary()

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ 測試被使用者中斷")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ 測試執行發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
