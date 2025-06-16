#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志系统模块
为整个项目提供统一的日志管理功能
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler

class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""
    
    # 定义颜色代码
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色  
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
        'RESET': '\033[0m'        # 重置
    }
    
    def format(self, record):
        """格式化日志记录"""
        # 获取原始格式化结果
        formatted = super().format(record)
        
        # 如果是控制台输出，添加颜色
        if hasattr(record, 'is_console') and record.is_console:
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            return f"{color}{formatted}{self.COLORS['RESET']}"
        
        return formatted

def setup_logger(name: str, log_level: str = 'INFO') -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        配置好的日志记录器
    """
    # 创建日志目录
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 创建格式化器
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # 文件处理器 - 滚动日志文件
    log_file = log_dir / f'{name}_{datetime.now().strftime("%Y%m%d")}.log'
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(console_formatter)
    
    # 为控制台记录添加标记
    class ConsoleFilter(logging.Filter):
        def filter(self, record):
            record.is_console = True
            return True
    
    console_handler.addFilter(ConsoleFilter())
    
    # 添加处理器到日志记录器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # 防止日志向上传播
    logger.propagate = False
    
    return logger

def get_log_files() -> list:
    """
    获取所有日志文件列表
    
    Returns:
        日志文件路径列表
    """
    log_dir = Path('logs')
    if not log_dir.exists():
        return []
    
    # 获取所有.log文件，按修改时间排序
    log_files = []
    for file_path in log_dir.glob('*.log'):
        if file_path.is_file():
            log_files.append({
                'path': str(file_path),
                'name': file_path.name,
                'size': file_path.stat().st_size,
                'modified': datetime.fromtimestamp(file_path.stat().st_mtime)
            })
    
    # 按修改时间降序排序
    log_files.sort(key=lambda x: x['modified'], reverse=True)
    
    return log_files

def read_log_file(file_path: str, lines: int = 100) -> list:
    """
    读取日志文件的最后几行
    
    Args:
        file_path: 日志文件路径
        lines: 读取的行数
    
    Returns:
        日志行列表
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            # 返回最后的lines行
            return all_lines[-lines:] if len(all_lines) > lines else all_lines
    except Exception as e:
        return [f"读取日志文件失败: {str(e)}"]

def cleanup_old_logs(days: int = 30):
    """
    清理旧的日志文件
    
    Args:
        days: 保留天数，超过此天数的日志文件将被删除
    """
    log_dir = Path('logs')
    if not log_dir.exists():
        return
    
    cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
    
    for file_path in log_dir.glob('*.log*'):
        if file_path.is_file():
            file_time = file_path.stat().st_mtime
            if file_time < cutoff_time:
                try:
                    file_path.unlink()
                    print(f"删除过期日志文件: {file_path.name}")
                except Exception as e:
                    print(f"删除日志文件失败 {file_path.name}: {e}")

class LogContext:
    """日志上下文管理器"""
    
    def __init__(self, logger: logging.Logger, operation: str):
        """
        初始化日志上下文
        
        Args:
            logger: 日志记录器
            operation: 操作描述
        """
        self.logger = logger
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        """进入上下文"""
        self.start_time = datetime.now()
        self.logger.info(f"开始执行: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.info(f"完成执行: {self.operation} (耗时: {duration:.2f}秒)")
        else:
            self.logger.error(f"执行失败: {self.operation} - {exc_val} (耗时: {duration:.2f}秒)")
        
        return False  # 不抑制异常

# 默认日志记录器
default_logger = setup_logger('AutoFish')

# 便捷函数
def log_info(message: str, logger_name: str = 'AutoFish'):
    """记录信息日志"""
    logger = logging.getLogger(logger_name)
    logger.info(message)

def log_error(message: str, logger_name: str = 'AutoFish'):
    """记录错误日志"""
    logger = logging.getLogger(logger_name)
    logger.error(message)

def log_warning(message: str, logger_name: str = 'AutoFish'):
    """记录警告日志"""
    logger = logging.getLogger(logger_name)
    logger.warning(message)

def log_debug(message: str, logger_name: str = 'AutoFish'):
    """记录调试日志"""
    logger = logging.getLogger(logger_name)
    logger.debug(message)

if __name__ == "__main__":
    # 测试日志系统
    test_logger = setup_logger('Test')
    
    test_logger.debug("这是调试信息")
    test_logger.info("这是普通信息") 
    test_logger.warning("这是警告信息")
    test_logger.error("这是错误信息")
    test_logger.critical("这是严重错误信息")
    
    # 测试日志上下文
    with LogContext(test_logger, "测试操作"):
        import time
        time.sleep(1)
        test_logger.info("操作进行中...")
    
    print("日志测试完成，请查看logs目录") 