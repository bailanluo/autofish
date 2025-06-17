#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AutoFish钓鱼脚本新版主入口

使用重构后的精简架构启动钓鱼程序。
"""

import os
import sys
import logging
import ctypes
import subprocess
from pathlib import Path

# 确保可以导入模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))  # 项目根目录
sys.path.insert(0, parent_dir)

# 导入相关模块
from modules.logger import setup_logger
from modules.auto_fisher.ui import FishingUI


def is_admin():
    """
    检查当前程序是否以管理员身份运行
    
    Returns:
        bool: 是否以管理员身份运行
    """
    try:
        if os.name == 'nt':
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    except Exception:
        return False


def restart_as_admin():
    """以管理员身份重新启动程序"""
    if os.name == 'nt':
        args = ' '.join(sys.argv)
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, args, None, 1
        )
    else:
        args = ['sudo', sys.executable] + sys.argv
        subprocess.Popen(args)


def main():
    """主函数"""
    # 检查管理员权限
    if not is_admin():
        print("需要管理员权限运行，正在尝试重新启动...")
        restart_as_admin()
        sys.exit(0)
    
    # 创建日志目录
    log_dir = os.path.join(parent_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # 设置日志
    logger = setup_logger('auto_fisher_new')
    logger.setLevel(logging.DEBUG)
    
    # 记录启动信息
    logger.info("=" * 50)
    logger.info("AutoFish钓鱼脚本 v2.4 重构版启动")
    logger.info(f"项目根目录: {parent_dir}")
    logger.info(f"Python版本: {sys.version}")
    logger.info("以管理员身份运行: 是")
    logger.info("=" * 50)
    
    try:
        # 创建并运行UI
        app = FishingUI()
        logger.info("启动钓鱼程序UI")
        app.run()
        
    except Exception as e:
        logger.error(f"运行钓鱼程序出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    
    finally:
        logger.info("AutoFish钓鱼脚本结束")
        sys.exit(0)


if __name__ == '__main__':
    main() 