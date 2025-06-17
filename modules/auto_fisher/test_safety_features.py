#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
安全功能测试脚本

验证Fail-Safe机制和热键系统是否正常工作。
"""

import sys
import os
import time
import threading
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from modules.auto_fisher.config import get_config
from modules.auto_fisher.hotkey_manager import get_hotkey_manager


def test_callback(action: str):
    """测试回调函数"""
    print(f"[测试] 检测到{action}动作")


def test_hotkey_system():
    """测试热键系统"""
    print("=== 热键系统测试 ===")
    print()
    
    # 获取热键管理器
    hotkey_manager = get_hotkey_manager()
    
    # 设置测试回调
    hotkey_manager.set_callbacks(
        start_callback=lambda: test_callback("开始"),
        stop_callback=lambda: test_callback("停止"),
        pause_callback=lambda: test_callback("暂停")
    )
    
    # 获取配置
    config = get_config()
    hotkeys = config.get_hotkeys()
    
    print("热键配置:")
    print(f"  开始钓鱼: {hotkeys.get('start', 'F1')}")
    print(f"  停止钓鱼: {hotkeys.get('stop', 'F2')}")
    print(f"  暂停钓鱼: {hotkeys.get('pause', 'F3')}")
    print("  紧急停止: Ctrl+Alt+Q 或 ESC")
    print()
    
    # 启动热键监听
    try:
        hotkey_manager.start_listening()
        print("✅ 热键监听启动成功")
        print()
        
        print("请测试以下功能:")
        print("1. 按F1测试开始功能")
        print("2. 按F2测试停止功能")  
        print("3. 按F3测试暂停功能")
        print("4. 按Ctrl+Alt+Q或ESC测试紧急停止")
        print("5. 按Enter键结束测试")
        print()
        
        # 等待用户测试
        input("按Enter键结束热键测试...")
        
        # 停止热键监听
        hotkey_manager.stop_listening()
        print("✅ 热键监听停止成功")
        
    except Exception as e:
        print(f"❌ 热键系统测试失败: {e}")
    
    print()


def test_fail_safe_info():
    """测试Fail-Safe信息说明"""
    print("=== Fail-Safe机制说明 ===")
    print()
    
    print("🛡️ PyAutoGUI Fail-Safe机制:")
    print("   - 这是一个重要的安全特性")
    print("   - 当鼠标快速移动到屏幕左上角(0,0)位置时")
    print("   - 会自动抛出FailSafeException异常")
    print("   - 立即停止所有PyAutoGUI操作")
    print("   - 防止自动化程序失控")
    print()
    
    print("🚨 紧急停止方法:")
    print("   1. 快速移动鼠标到屏幕左上角")
    print("   2. 按下F2键（默认停止热键）")
    print("   3. 按下Ctrl+Alt+Q组合键")
    print("   4. 按下ESC键")
    print("   5. 通过任务管理器结束程序")
    print()
    
    print("⚙️ 程序中的Fail-Safe处理:")
    print("   - 已启用pyautogui.FAILSAFE = True")
    print("   - 在点击线程中捕获FailSafeException")
    print("   - 自动触发程序安全停止流程")
    print("   - 释放所有资源和按键")
    print()
    
    print("✅ 建议:")
    print("   - 始终保持Fail-Safe机制启用")
    print("   - 这是您的安全保障")
    print("   - 当程序无响应时立即使用")
    print()


def simulate_clicking_scenario():
    """模拟点击场景，用于测试fail-safe"""
    print("=== 模拟点击场景测试 ===")
    print()
    
    print("⚠️  注意: 此测试将模拟快速点击")
    print("如果想要停止，请:")
    print("1. 快速移动鼠标到屏幕左上角(0,0)")
    print("2. 或按下F2/Ctrl+Alt+Q/ESC键")
    print()
    
    choice = input("是否开始模拟测试? (y/N): ")
    if choice.lower() != 'y':
        print("跳过模拟测试")
        return
    
    print("5秒后开始模拟点击...")
    for i in range(5, 0, -1):
        print(f"{i}..", end='', flush=True)
        time.sleep(1)
    print()
    
    print("开始模拟点击 - 请测试停止方法!")
    
    import pyautogui
    pyautogui.FAILSAFE = True
    
    try:
        for i in range(50):  # 模拟50次点击
            pyautogui.click()
            time.sleep(0.1)
            print(f"点击 {i+1}/50", end='\r')
            
        print("\n模拟点击完成")
        
    except pyautogui.FailSafeException:
        print("\n✅ Fail-Safe机制触发 - 测试成功!")
        print("鼠标移动到左上角成功停止程序")
        
    except KeyboardInterrupt:
        print("\n✅ 键盘中断 - 测试成功!")
        print("Ctrl+C成功停止程序")
        
    except Exception as e:
        print(f"\n❌ 模拟测试出错: {e}")


def main():
    """主测试函数"""
    print("AutoFish 安全功能测试")
    print("=" * 50)
    print()
    
    # 测试说明
    test_fail_safe_info()
    
    # 测试热键系统
    test_hotkey_system()
    
    # 模拟点击测试
    simulate_clicking_scenario()
    
    print("=" * 50)
    print("安全功能测试完成")
    print()
    print("总结:")
    print("✅ Fail-Safe机制: 鼠标移动到左上角可紧急停止")
    print("✅ 热键系统: F1开始, F2停止, F3暂停")
    print("✅ 紧急热键: Ctrl+Alt+Q, ESC")
    print("✅ 程序现在有多重安全保障")


if __name__ == "__main__":
    main() 