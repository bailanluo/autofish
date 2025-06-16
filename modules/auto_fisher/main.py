#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AutoFish钓鱼脚本主入口模块

该模块是AutoFish钓鱼脚本的主入口，负责初始化日志系统和启动UI。
"""

import os
import sys
import logging
import argparse
import ctypes
import subprocess
from pathlib import Path

# 确保可以导入模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))  # 项目根目录
sys.path.insert(0, parent_dir)

# 导入相关模块
from modules.logger import setup_logger
from modules.auto_fisher.ui_manager import get_instance as get_ui_manager


def is_admin():
    """
    检查当前程序是否以管理员身份运行
    
    Returns:
        bool: 是否以管理员身份运行
    """
    try:
        # Windows系统下检查管理员权限
        if os.name == 'nt':
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        # Linux/Mac系统下检查root权限
        else:
            return os.geteuid() == 0
    except Exception:
        return False


def restart_as_admin():
    """
    以管理员身份重新启动程序
    """
    if os.name == 'nt':  # Windows系统
        # 构建命令行参数
        args = ' '.join(sys.argv)
        # 使用subprocess以管理员身份启动新进程
        ctypes.windll.shell32.ShellExecuteW(
            None,           # 父窗口句柄
            "runas",        # 操作: runas表示以管理员身份运行
            sys.executable, # 程序路径
            args,           # 命令行参数
            None,           # 工作目录
            1               # 显示方式: 1表示正常显示
        )
    else:  # Linux/Mac系统
        args = ['sudo', sys.executable] + sys.argv
        subprocess.Popen(args)


def main():
    """
    钓鱼脚本主函数
    """
    # 检查管理员权限
    if not is_admin():
        print("需要管理员权限运行，正在尝试重新启动...")
        restart_as_admin()
        sys.exit(0)
        
    # 创建日志目录
    log_dir = os.path.join(parent_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # 设置日志
    logger = setup_logger('auto_fisher')
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='AutoFish - 自动钓鱼脚本')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    args = parser.parse_args()
    
    # 默认启用调试模式，设置日志级别为DEBUG
    logger.setLevel(logging.DEBUG)
    logger.info("已启用调试模式")
    
    # 记录启动日志
    logger.info("AutoFish钓鱼脚本启动")
    logger.info(f"项目根目录: {parent_dir}")
    logger.info(f"Python版本: {sys.version}")
    logger.info("以管理员身份运行: 是")
    
    try:
        # 获取UI管理器
        ui_manager = get_ui_manager()
        
        # 运行UI
        logger.info("启动UI主循环")
        ui_manager.run()
        
    except Exception as e:
        logger.error(f"运行钓鱼脚本出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    
    finally:
        logger.info("AutoFish钓鱼脚本结束")
        # 确保程序完全退出
        sys.exit(0)


if __name__ == '__main__':
    main() 