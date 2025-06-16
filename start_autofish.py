#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AutoFish 启动脚本

该脚本用于启动AutoFish钓鱼程序，支持以管理员权限运行
"""

import os
import sys
import argparse
import logging
import traceback
import time

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='启动AutoFish钓鱼程序')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--log-level', type=str, default='INFO', 
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='日志级别')
    args = parser.parse_args()
    
    try:
        # 设置日志级别
        log_level = getattr(logging, args.log_level)
        
        # 初始化日志系统
        from modules.logger import setup_logger
        logger = setup_logger('AutoFish', args.log_level)
        
        # 记录启动信息
        logging.info("=" * 50)
        logging.info("AutoFish 钓鱼程序启动")
        logging.info(f"日志级别: {args.log_level}")
        logging.info(f"调试模式: {'启用' if args.debug else '禁用'}")
        logging.info("=" * 50)
        
        # 导入业务逻辑模块（这里延迟导入，确保日志系统已经初始化）
        from modules.auto_fisher.business_logic import BusinessLogic
        
        # 创建业务逻辑实例
        logging.info("初始化业务逻辑...")
        business_logic = BusinessLogic()
        
        # 启动热键监听
        logging.info("启动热键监听...")
        business_logic.start_hotkey_listener()
        
        # 输出热键信息
        hotkeys = business_logic.config_manager.get_hotkeys()
        logging.info(f"开始/停止热键: {hotkeys.get('start', 'Ctrl+Alt+Y')}")
        logging.info(f"紧急停止热键: {hotkeys.get('stop', 'Ctrl+Alt+Q')}")
        
        # 等待程序结束（通过热键控制）
        logging.info("钓鱼程序已启动，使用热键控制...")
        logging.info("按下热键开始/停止钓鱼，按Ctrl+C退出程序")
        
        # 等待用户按下Ctrl+C
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info("检测到Ctrl+C，准备退出程序")
        
        # 停止钓鱼
        if business_logic.is_fishing_active():
            logging.info("正在停止钓鱼...")
            business_logic.stop_fishing()
        
        # 停止热键监听
        business_logic.stop_hotkey_listener()
        
        logging.info("程序正常退出")
        
    except Exception as e:
        logging.critical(f"启动钓鱼程序时发生错误: {str(e)}")
        logging.critical(traceback.format_exc())
        return 1
    
    logging.info("钓鱼程序已退出")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 