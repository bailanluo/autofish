#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AutoFish重构版本测试脚本

测试重构后的各个模块是否能正常工作。
"""

import os
import sys
import time
import logging
from pathlib import Path

# 确保可以导入模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))  # 项目根目录
sys.path.insert(0, parent_dir)

# 导入模块
from modules.logger import setup_logger


def test_config():
    """测试配置模块"""
    print("测试配置模块...")
    try:
        from modules.auto_fisher.config import get_config
        
        config = get_config()
        print(f"✓ 配置模块初始化成功")
        print(f"  - 模型路径: {config.get_model_path()}")
        print(f"  - OCR路径: {config.get_tesseract_path()}")
        print(f"  - 状态映射: {config.get('state_mapping')}")
        
        return True
    except Exception as e:
        print(f"✗ 配置模块测试失败: {e}")
        return False


def test_state_detector():
    """测试状态检测器"""
    print("\n测试状态检测器...")
    try:
        from modules.auto_fisher.state_detector import get_detector
        
        detector = get_detector()
        print(f"✓ 状态检测器初始化成功")
        print(f"  - 模型是否加载: {'是' if detector.model else '否'}")
        print(f"  - 状态名称映射: {detector.state_names}")
        
        # 测试屏幕捕获
        image = detector.capture_screen()
        if image is not None:
            print(f"  - 屏幕捕获成功: {image.shape}")
        else:
            print(f"  - 屏幕捕获失败")
        
        return True
    except Exception as e:
        print(f"✗ 状态检测器测试失败: {e}")
        return False


def test_input_controller():
    """测试输入控制器"""
    print("\n测试输入控制器...")
    try:
        from modules.auto_fisher.input_controller import get_input_controller
        
        controller = get_input_controller()
        print(f"✓ 输入控制器初始化成功")
        print(f"  - 点击状态: {'活跃' if controller.is_clicking() else '停止'}")
        print(f"  - 当前按键: {controller.current_key_pressed}")
        
        return True
    except Exception as e:
        print(f"✗ 输入控制器测试失败: {e}")
        return False


def test_fishing_controller():
    """测试钓鱼控制器"""
    print("\n测试钓鱼控制器...")
    try:
        from modules.auto_fisher.fishing_controller import get_fishing_controller, FishingState
        
        controller = get_fishing_controller()
        print(f"✓ 钓鱼控制器初始化成功")
        print(f"  - 当前状态: {controller.get_current_state()}")
        print(f"  - 是否活跃: {'是' if controller.is_active() else '否'}")
        print(f"  - 状态枚举: {list(FishingState)}")
        
        return True
    except Exception as e:
        print(f"✗ 钓鱼控制器测试失败: {e}")
        return False


def test_ui_creation():
    """测试UI创建（不启动）"""
    print("\n测试UI创建...")
    try:
        from modules.auto_fisher.ui import FishingUI, StatusWindow, SettingsDialog
        
        print(f"✓ UI模块导入成功")
        print(f"  - FishingUI类: 可用")
        print(f"  - StatusWindow类: 可用")
        print(f"  - SettingsDialog类: 可用")
        
        return True
    except Exception as e:
        print(f"✗ UI模块测试失败: {e}")
        return False


def main():
    """主测试函数"""
    # 设置日志
    logger = setup_logger('test_refactored')
    logger.setLevel(logging.DEBUG)
    
    print("AutoFish v2.4 重构版本测试")
    print("=" * 40)
    
    # 运行测试
    tests = [
        ("配置模块", test_config),
        ("状态检测器", test_state_detector),
        ("输入控制器", test_input_controller),
        ("钓鱼控制器", test_fishing_controller),
        ("UI模块", test_ui_creation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"✗ {test_name}测试出现异常: {e}")
    
    print("\n" + "=" * 40)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！重构版本可以使用")
        print("\n启动方式:")
        print("python modules/auto_fisher/new_main.py")
    else:
        print("❌ 部分测试失败，需要修复问题")
    
    print("=" * 40)


if __name__ == '__main__':
    main() 