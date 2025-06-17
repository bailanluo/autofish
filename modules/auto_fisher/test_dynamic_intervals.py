#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
动态检测间隔测试脚本

验证不同状态下的检测间隔配置是否正确工作。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from modules.auto_fisher.config import get_config
from modules.auto_fisher.fishing_controller import FishingController, FishingState


def test_dynamic_intervals():
    """测试动态检测间隔"""
    print("=== 动态检测间隔测试 ===")
    
    # 获取配置实例
    config = get_config()
    controller = FishingController()
    
    # 测试不同状态的检测间隔
    states_to_test = [
        (FishingState.IDLE, "idle"),
        (FishingState.WAITING, "waiting"),
        (FishingState.FISH_HOOKED, "fish_hooked"),
        (FishingState.PULLING_NORMAL, "pulling"),
        (FishingState.PULLING_HALFWAY, "pulling"),
        (FishingState.SUCCESS, "success")
    ]
    
    print("\n主循环检测间隔:")
    print("-" * 50)
    for state, expected_type in states_to_test:
        controller.current_state = state
        interval = controller._get_current_detection_interval()
        expected_interval = config.get_detection_interval(expected_type)
        
        print(f"{state.name:20} : {interval:.3f}s (预期: {expected_interval:.3f}s) {'✓' if interval == expected_interval else '✗'}")
    
    # 测试OCR检测间隔
    print("\nOCR检测间隔:")
    print("-" * 50)
    ocr_states_to_test = [
        (FishingState.PULLING_NORMAL, "pulling_normal"),
        (FishingState.PULLING_HALFWAY, "pulling_halfway"),
        (FishingState.IDLE, "default")
    ]
    
    for state, expected_type in ocr_states_to_test:
        controller.current_state = state
        interval = controller._get_current_ocr_detection_interval()
        expected_interval = config.get_ocr_detection_interval(expected_type)
        
        print(f"{state.name:20} : {interval:.3f}s (预期: {expected_interval:.3f}s) {'✓' if interval == expected_interval else '✗'}")
    
    # 显示配置详情
    print("\n配置详情:")
    print("-" * 50)
    print("主循环动态间隔配置:")
    dynamic_intervals = config.get('model.dynamic_intervals', {})
    for state_type, interval in dynamic_intervals.items():
        print(f"  {state_type:15} : {interval:.3f}s")
    
    print("\nOCR动态间隔配置:")
    ocr_dynamic_intervals = config.get('ocr.dynamic_intervals', {})
    for state_type, interval in ocr_dynamic_intervals.items():
        print(f"  {state_type:15} : {interval:.3f}s")
    
    print("\n性能对比:")
    print("-" * 50)
    old_interval = 0.1  # 用户之前设置的间隔
    new_fast_interval = config.get_detection_interval("fish_hooked")
    improvement = (old_interval - new_fast_interval) / old_interval * 100
    
    print(f"旧检测间隔 (固定) : {old_interval:.3f}s")
    print(f"新检测间隔 (鱼上钩): {new_fast_interval:.3f}s")
    print(f"响应速度提升     : {improvement:.1f}%")
    print(f"每秒检测次数提升 : {1/new_fast_interval:.1f} vs {1/old_interval:.1f}")


if __name__ == "__main__":
    test_dynamic_intervals() 