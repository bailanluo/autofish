"""
通用图像数据采集工具模块
独立的数据采集工具，便于移植和复用
"""

from .config_manager import DataCollectorConfig
from .screen_capture import ScreenCapture
from .data_manager import DataManager
from .hotkey_listener import HotkeyListener
from .main import DataCollectorApp

__version__ = "2.0.0"
__author__ = "AI Assistant"
__description__ = "通用图像数据采集工具"

# 导出主要类
__all__ = [
    'DataCollectorConfig',
    'ScreenCapture', 
    'DataManager',
    'HotkeyListener',
    'DataCollectorApp'
] 