#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AutoFish UI测试脚本

用于测试UI界面显示是否正常。
"""

import os
import sys
import tkinter as tk
from pathlib import Path

# 确保可以导入模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))  # 项目根目录
sys.path.insert(0, parent_dir)

from modules.logger import setup_logger


def test_ui_layout():
    """测试UI布局"""
    try:
        # 导入UI模块
        from modules.auto_fisher.ui import FishingUI, StatusWindow, SettingsDialog
        
        print("✓ UI模块导入成功")
        
        # 创建主窗口（不运行主循环）
        app = FishingUI()
        print("✓ 主界面创建成功")
        
        # 获取窗口信息
        app.root.update_idletasks()
        width = app.root.winfo_width()
        height = app.root.winfo_height()
        print(f"✓ 主窗口尺寸: {width}x{height}")
        
        # 测试状态窗口
        app.status_window.create_window(app.root)
        print("✓ 状态窗口创建成功")
        
        # 测试设置对话框
        settings = SettingsDialog(app.root)
        print("✓ 设置对话框创建成功")
        
        # 显示窗口3秒钟
        print("\n[信息] 显示界面3秒钟进行视觉检查...")
        app.root.after(3000, app.root.quit)  # 3秒后关闭
        app.root.mainloop()
        
        print("✓ UI测试完成")
        return True
        
    except Exception as e:
        print(f"✗ UI测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("AutoFish UI界面测试")
    print("=" * 30)
    
    # 设置日志
    logger = setup_logger('test_ui')
    
    # 运行测试
    success = test_ui_layout()
    
    print("\n" + "=" * 30)
    if success:
        print("🎉 UI测试通过！界面显示正常")
    else:
        print("❌ UI测试失败，需要修复问题")
    
    print("=" * 30)


if __name__ == '__main__':
    main() 