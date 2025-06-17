"""
Fisher钓鱼模块
智能钓鱼辅助工具的核心钓鱼模块

作者: AutoFish Team
版本: v1.0
创建时间: 2024-12-28
"""

__version__ = "1.0.0"
__author__ = "AutoFish Team"
__description__ = "智能钓鱼辅助模块"

# 导入核心组件
from .config import FisherConfig
from .fishing_controller import FishingController
from .ui import FisherUI

__all__ = [
    'FisherConfig',
    'FishingController', 
    'FisherUI'
] 