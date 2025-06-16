#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动钓鱼项目模块包
包含数据采集、模型训练、自动钓鱼等核心模块
"""

__version__ = '2.0.0'
__author__ = 'AutoFish Team'
__description__ = '自动钓鱼项目核心模块'

# 模块版本信息
MODULES = {
    'data_collector': '数据采集模块',
    'model_trainer': '模型训练模块', 
    'auto_fisher': '自动钓鱼模块',
    'logger': '日志系统模块'
}

def get_module_info():
    """获取模块信息"""
    return {
        'version': __version__,
        'author': __author__,
        'description': __description__,
        'modules': MODULES
    } 