"""
測試模糊圖層功能
測試項目：
1. 配置載入與驗證
2. 距離到模糊參數的映射計算
3. 緩動函數計算
4. 參數邊界檢查
5. 完整系統整合測試
"""

import sys
import json
from pathlib import Path
import math

# 測試結果統計
test_results = {
    'passed': 0,
    'failed': 0,
    'errors': []
}

def print_section(title):
    """列印測試區段標題"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def test_assert(condition, test_name, error_msg=""):
    """斷言測試結果"""
    if condition:
        print(f"✅ {test_name}")
        test_results['passed'] += 1
        return True
    else:
        print(f"❌ {test_name}")
        if error_msg:
            print(f"   錯誤: {error_msg}")
        test_results['failed'] += 1
        test_results['errors'].append(test_name)
        return False

def calculate_normalized_distance(distance, min_dist, max_dist):
    """計算正規化距離 (0-1)"""
    if distance <= min_dist:
        return 0.0
    if distance >= max_dist:
        return 1.0
    return (distance - min_dist) / (max_dist - min_dist)

def apply_easing(t, easing_type):
    """套用緩動函數"""
    t = max(0.0, min(1.0, t))  # 確保在 0-1 範圍內
    
    if easing_type == 'linear':
        return t
    elif easing_type == 'ease-in':
        return t * t
    elif easing_type == 'ease-out':
        return 1 - math.pow(1 - t, 2)
    elif easing_type == 'ease-in-out':
        if t < 0.5:
            return 2 * t * t
        else:
            return 1 - math.pow(-2 * t + 2, 2) / 2
    else:
        return t

def lerp(start, end, t):
    """線性插值"""
    return start + (end - start) * t

def calculate_blur_params(distance, config):
    """計算給定距離下的模糊參數"""
    # 正規化距離
    normalized = calculate_normalized_distance(
        distance,
        config['min_distance'],
        config['max_distance']
    )
    
    # 套用緩動函數
    eased = apply_easing(normalized, config['easing_function'])
    
    # 計算模糊半徑和透明度（距離越近，模糊越強）
    blur_radius = lerp(config['max_blur_radius'], config['min_blur_radius'], eased)
    opacity = lerp(config['max_opacity'], config['min_opacity'], eased)
    
    return {
        'normalized': normalized,
        'eased': eased,
        'blur_radius': blur_radius,
        'opacity': opacity
    }

# ==================== 測試 1: 配置載入 ====================
def test_config_loading():
    """測試配置檔案載入"""
    print_section("測試 1: 配置檔案載入")
    
    config_path = Path(__file__).parent / 'backend' / 'configs' / 'project_config.json'
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        test_assert('blur_overlay' in config, "配置檔案包含 blur_overlay")
        
        blur_config = config['blur_overlay']
        
        # 檢查必要欄位
        required_fields = [
            'enabled', 'min_distance', 'max_distance',
            'min_blur_radius', 'max_blur_radius',
            'min_opacity', 'max_opacity',
            'overlay_color', 'easing_function',
            'layer_count', 'blend_mode'
        ]
        
        for field in required_fields:
            test_assert(
                field in blur_config,
                f"包含必要欄位: {field}"
            )
        
        return config
        
    except Exception as e:
        test_assert(False, "配置檔案載入", str(e))
        return None

# ==================== 測試 2: 參數驗證 ====================
def test_parameter_validation(config):
    """測試參數驗證"""
    print_section("測試 2: 參數範圍驗證")
    
    if not config:
        print("⚠️ 跳過測試（配置未載入）")
        return
    
    blur_config = config['blur_overlay']
    
    # 距離範圍
    test_assert(
        blur_config['min_distance'] < blur_config['max_distance'],
        "最小距離 < 最大距離",
        f"min={blur_config['min_distance']}, max={blur_config['max_distance']}"
    )
    
    test_assert(
        blur_config['min_distance'] >= 0,
        "最小距離 >= 0"
    )
    
    # 模糊半徑範圍
    test_assert(
        blur_config['min_blur_radius'] >= 0,
        "最小模糊半徑 >= 0"
    )
    
    test_assert(
        blur_config['max_blur_radius'] >= blur_config['min_blur_radius'],
        "最大模糊半徑 >= 最小模糊半徑"
    )
    
    test_assert(
        blur_config['max_blur_radius'] <= 50,
        "最大模糊半徑 <= 50 (效能考量)",
        f"實際值: {blur_config['max_blur_radius']}"
    )
    
    # 透明度範圍
    test_assert(
        0 <= blur_config['min_opacity'] <= 1,
        "最小透明度在 0-1 範圍",
        f"實際值: {blur_config['min_opacity']}"
    )
    
    test_assert(
        0 <= blur_config['max_opacity'] <= 1,
        "最大透明度在 0-1 範圍",
        f"實際值: {blur_config['max_opacity']}"
    )
    
    test_assert(
        blur_config['max_opacity'] >= blur_config['min_opacity'],
        "最大透明度 >= 最小透明度"
    )
    
    # 圖層數量
    test_assert(
        1 <= blur_config['layer_count'] <= 10,
        "圖層數量在 1-10 範圍",
        f"實際值: {blur_config['layer_count']}"
    )
    
    # 緩動函數
    valid_easing = ['linear', 'ease-in', 'ease-out', 'ease-in-out']
    test_assert(
        blur_config['easing_function'] in valid_easing,
        f"緩動函數有效: {blur_config['easing_function']}"
    )
    
    # 混合模式
    valid_blend_modes = ['normal', 'multiply', 'screen', 'overlay', 'soft-light']
    test_assert(
        blur_config['blend_mode'] in valid_blend_modes,
        f"混合模式有效: {blur_config['blend_mode']}"
    )
    
    # 顏色格式
    color = blur_config['overlay_color']
    test_assert(
        color.startswith('#') and len(color) == 7,
        f"顏色格式正確: {color}"
    )

# ==================== 測試 3: 距離映射計算 ====================
def test_distance_mapping(config):
    """測試距離到參數的映射計算"""
    print_section("測試 3: 距離映射計算")
    
    if not config:
        print("⚠️ 跳過測試（配置未載入）")
        return
    
    blur_config = config['blur_overlay']
    
    # 測試邊界情況
    print("\n📊 邊界情況測試:")
    
    # 最小距離
    params = calculate_blur_params(blur_config['min_distance'], blur_config)
    test_assert(
        abs(params['normalized'] - 0.0) < 0.001,
        f"最小距離 ({blur_config['min_distance']}cm) -> normalized=0",
        f"實際值: {params['normalized']:.3f}"
    )
    test_assert(
        abs(params['blur_radius'] - blur_config['max_blur_radius']) < 0.001,
        f"最小距離 -> 最大模糊半徑",
        f"預期: {blur_config['max_blur_radius']}, 實際: {params['blur_radius']:.2f}"
    )
    
    # 最大距離
    params = calculate_blur_params(blur_config['max_distance'], blur_config)
    test_assert(
        abs(params['normalized'] - 1.0) < 0.001,
        f"最大距離 ({blur_config['max_distance']}cm) -> normalized=1",
        f"實際值: {params['normalized']:.3f}"
    )
    test_assert(
        abs(params['blur_radius'] - blur_config['min_blur_radius']) < 0.001,
        f"最大距離 -> 最小模糊半徑",
        f"預期: {blur_config['min_blur_radius']}, 實際: {params['blur_radius']:.2f}"
    )
    
    # 測試中間值
    print("\n📊 中間值測試:")
    
    mid_distance = (blur_config['min_distance'] + blur_config['max_distance']) / 2
    params = calculate_blur_params(mid_distance, blur_config)
    
    print(f"   中間距離: {mid_distance}cm")
    print(f"   正規化值: {params['normalized']:.3f}")
    print(f"   緩動後: {params['eased']:.3f}")
    print(f"   模糊半徑: {params['blur_radius']:.2f}px")
    print(f"   透明度: {params['opacity']:.3f}")
    
    test_assert(
        0 < params['normalized'] < 1,
        "中間距離的正規化值在 0-1 之間"
    )
    
    # 測試超出範圍的情況
    print("\n📊 邊界外測試:")
    
    params_below = calculate_blur_params(blur_config['min_distance'] - 10, blur_config)
    test_assert(
        params_below['normalized'] == 0.0,
        "低於最小距離 -> normalized=0"
    )
    
    params_above = calculate_blur_params(blur_config['max_distance'] + 10, blur_config)
    test_assert(
        params_above['normalized'] == 1.0,
        "高於最大距離 -> normalized=1"
    )

# ==================== 測試 4: 緩動函數 ====================
def test_easing_functions():
    """測試緩動函數"""
    print_section("測試 4: 緩動函數計算")
    
    test_values = [0.0, 0.25, 0.5, 0.75, 1.0]
    easing_types = ['linear', 'ease-in', 'ease-out', 'ease-in-out']
    
    for easing_type in easing_types:
        print(f"\n📊 測試 {easing_type}:")
        
        for t in test_values:
            result = apply_easing(t, easing_type)
            
            # 基本驗證
            test_assert(
                0 <= result <= 1,
                f"  t={t:.2f} -> {result:.3f} (範圍檢查)"
            )
        
        # 邊界檢查
        test_assert(
            apply_easing(0.0, easing_type) == 0.0,
            f"{easing_type}: f(0) = 0"
        )
        test_assert(
            abs(apply_easing(1.0, easing_type) - 1.0) < 0.001,
            f"{easing_type}: f(1) = 1"
        )

# ==================== 測試 5: 完整情境測試 ====================
def test_full_scenarios(config):
    """測試完整使用情境"""
    print_section("測試 5: 完整使用情境")
    
    if not config:
        print("⚠️ 跳過測試（配置未載入）")
        return
    
    blur_config = config['blur_overlay']
    
    print("\n📊 情境 1: 使用者從遠到近移動")
    distances = [120, 110, 100, 90, 80, 70]
    
    prev_blur = None
    prev_opacity = None
    
    for dist in distances:
        params = calculate_blur_params(dist, blur_config)
        print(f"   {dist}cm -> 模糊: {params['blur_radius']:.2f}px, 透明度: {params['opacity']:.3f}")
        
        # 驗證趨勢：距離減少，模糊和透明度應該增加
        if prev_blur is not None:
            test_assert(
                params['blur_radius'] >= prev_blur,
                f"距離減少時模糊增加 ({dist}cm)"
            )
        if prev_opacity is not None:
            test_assert(
                params['opacity'] >= prev_opacity,
                f"距離減少時透明度增加 ({dist}cm)"
            )
        
        prev_blur = params['blur_radius']
        prev_opacity = params['opacity']
    
    print("\n📊 情境 2: 使用者從近到遠移動")
    distances = [70, 80, 90, 100, 110, 120]
    
    prev_blur = None
    prev_opacity = None
    
    for dist in distances:
        params = calculate_blur_params(dist, blur_config)
        print(f"   {dist}cm -> 模糊: {params['blur_radius']:.2f}px, 透明度: {params['opacity']:.3f}")
        
        # 驗證趨勢：距離增加，模糊和透明度應該減少
        if prev_blur is not None:
            test_assert(
                params['blur_radius'] <= prev_blur,
                f"距離增加時模糊減少 ({dist}cm)"
            )
        if prev_opacity is not None:
            test_assert(
                params['opacity'] <= prev_opacity,
                f"距離增加時透明度減少 ({dist}cm)"
            )
        
        prev_blur = params['blur_radius']
        prev_opacity = params['opacity']
    
    print("\n📊 情境 3: 不同緩動函數比較")
    test_distance = 90  # 中間值
    
    for easing in ['linear', 'ease-in', 'ease-out', 'ease-in-out']:
        test_config = blur_config.copy()
        test_config['easing_function'] = easing
        params = calculate_blur_params(test_distance, test_config)
        print(f"   {easing}: 模糊={params['blur_radius']:.2f}px, 透明度={params['opacity']:.3f}")

# ==================== 測試 6: 效能考量驗證 ====================
def test_performance_considerations(config):
    """測試效能相關的配置建議"""
    print_section("測試 6: 效能考量驗證")
    
    if not config:
        print("⚠️ 跳過測試（配置未載入）")
        return
    
    blur_config = config['blur_overlay']
    
    # 模糊半徑建議
    if blur_config['max_blur_radius'] <= 5:
        print("✅ 模糊半徑 <= 5px (高效能)")
    elif blur_config['max_blur_radius'] <= 10:
        print("⚠️ 模糊半徑 <= 10px (中等效能)")
    else:
        print("❗ 模糊半徑 > 10px (可能影響效能)")
    
    # 圖層數量建議
    if blur_config['layer_count'] <= 3:
        print("✅ 圖層數量 <= 3 (建議值)")
    elif blur_config['layer_count'] <= 5:
        print("⚠️ 圖層數量 <= 5 (尚可接受)")
    else:
        print("❗ 圖層數量 > 5 (可能影響效能)")
    
    # 組合效能評估
    performance_score = (
        (5 - min(blur_config['max_blur_radius'], 10)) / 5 * 0.6 +
        (5 - min(blur_config['layer_count'], 10)) / 5 * 0.4
    )
    
    print(f"\n📊 效能評分: {performance_score * 100:.1f}/100")
    
    if performance_score >= 0.8:
        print("✅ 配置效能優秀")
    elif performance_score >= 0.6:
        print("⚠️ 配置效能良好")
    else:
        print("❗ 配置可能影響效能，建議調整")

# ==================== 主測試流程 ====================
def main():
    """執行所有測試"""
    print("\n" + "="*60)
    print("  🧪 FlurPaint 模糊圖層功能測試")
    print("="*60)
    
    # 載入配置
    config = test_config_loading()
    
    # 執行所有測試
    test_parameter_validation(config)
    test_distance_mapping(config)
    test_easing_functions()
    test_full_scenarios(config)
    test_performance_considerations(config)
    
    # 測試總結
    print_section("測試總結")
    print(f"✅ 通過: {test_results['passed']}")
    print(f"❌ 失敗: {test_results['failed']}")
    
    if test_results['failed'] > 0:
        print("\n失敗的測試項目:")
        for error in test_results['errors']:
            print(f"  • {error}")
    
    total = test_results['passed'] + test_results['failed']
    success_rate = (test_results['passed'] / total * 100) if total > 0 else 0
    
    print(f"\n📊 成功率: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("\n🎉 所有測試通過！模糊圖層功能運作正常！")
        return 0
    elif success_rate >= 80:
        print("\n⚠️ 大部分測試通過，但有部分問題需要修正")
        return 1
    else:
        print("\n❌ 測試失敗過多，請檢查實作")
        return 2

if __name__ == "__main__":
    sys.exit(main())
