#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简单测试脚本

用于测试状态显示窗口的功能
"""

import os
import sys
import time
import logging

# 添加项目根目录到系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.insert(0, project_root)

# 设置日志级别
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# 导入相关模块
from modules.auto_fisher.status_display import get_instance as get_status_display

def main():
    """
    主函数
    """
    print("开始测试状态显示窗口...")
    
    # 获取状态显示实例
    status_display = get_status_display()
    
    # 启动状态显示窗口
    status_display.start()
    
    # 更新状态
    states = ["初始化中", "空闲", "等待上钩", "鱼上钩", "提线中", "提线过半", "向右拉", "向左拉", "钓鱼成功"]
    
    # 循环更新状态
    for state in states:
        print(f"更新状态: {state}")
        status_display.update_state(state)
        time.sleep(1)
    
    # 更新点击次数
    for i in range(1, 11):
        status_display.update_click_count(i * 10)
        time.sleep(0.5)
    
    # 更新方向
    directions = ["无", "向左", "向右"]
    for direction in directions:
        status_display.update_direction(direction)
        time.sleep(1)
    
    print("测试完成，窗口将在5秒后关闭...")
    time.sleep(5)
    
    # 停止状态显示窗口
    status_display.stop()
    
    print("测试结束")

if __name__ == "__main__":
    main() 