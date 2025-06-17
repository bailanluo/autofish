#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置管理器模块

该模块负责加载和管理钓鱼脚本的配置信息，提供统一的配置访问接口。
"""

import os
import yaml
import logging
from pathlib import Path

class ConfigManager:
    """
    配置管理器类
    
    负责加载、验证和提供钓鱼脚本配置信息的访问。
    """
    
    def __init__(self, config_path=None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，如果不提供，则使用默认路径
        """
        # 项目根目录
        self.root_dir = Path(os.path.abspath(__file__)).parent.parent.parent
        
        # 默认配置路径
        self.config_path = config_path or os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")
        
        # 配置数据
        self.config = None
        
        # 加载配置
        self.load_config()
    
    def load_config(self):
        """
        加载配置文件
        
        从指定路径加载YAML配置文件，并进行基本验证
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                self.config = yaml.safe_load(file)
                
            # 执行配置验证
            self._validate_config()
            
            logging.info(f"成功加载钓鱼脚本配置: {self.config_path}")
            
        except Exception as e:
            logging.error(f"加载配置文件失败: {str(e)}")
            raise RuntimeError(f"无法加载配置文件: {str(e)}")
    
    def _validate_config(self):
        """
        验证配置是否包含所有必需的键
        """
        # 必需的顶级配置键
        required_keys = ['model', 'fishing', 'hotkeys', 'display', 'ui']
        
        # 检查顶级键
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"配置缺少必需的键: {key}")
        
        # 检查模型配置
        model_keys = ['path', 'confidence', 'fps', 'class_mapping']
        for key in model_keys:
            if key not in self.config['model']:
                raise ValueError(f"模型配置缺少必需的键: {key}")
        
        # 检查类别映射表
        for i in range(7):  # 根据需求，我们应该有0-6的映射
            if i not in self.config['model']['class_mapping']:
                raise ValueError(f"类别映射表缺少必需的键: {i}")
    
    def save_config(self):
        """
        保存配置到文件
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as file:
                yaml.dump(self.config, file, default_flow_style=False, allow_unicode=True)
            
            logging.info(f"配置已保存到: {self.config_path}")
            
        except Exception as e:
            logging.error(f"保存配置文件失败: {str(e)}")
            raise RuntimeError(f"无法保存配置文件: {str(e)}")
    
    def get_config(self, section=None):
        """
        获取配置信息
        
        Args:
            section: 要获取的配置部分，如果为None则返回整个配置
        
        Returns:
            指定部分或整个配置的字典
        """
        if section is None:
            return self.config
        
        if section in self.config:
            return self.config[section]
        
        raise ValueError(f"配置中不存在部分: {section}")
    
    def update_config(self, section, key, value):
        """
        更新配置值
        
        Args:
            section: 要更新的配置部分
            key: 要更新的配置键
            value: 新的配置值
        """
        if section not in self.config:
            raise ValueError(f"配置中不存在部分: {section}")
        
        self.config[section][key] = value
    
    def get_model_path(self):
        """获取模型路径"""
        return os.path.join(self.root_dir, self.config['model']['path'])
    
    def get_model_confidence(self):
        """获取模型置信度阈值"""
        return self.config['model']['confidence']
    
    def get_model_fps(self):
        """获取检测帧率"""
        return self.config['model']['fps']
    
    def get_class_mapping(self):
        """获取类别映射表"""
        return self.config['model']['class_mapping']
    
    def get_click_interval(self):
        """获取点击间隔范围"""
        return (
            self.config['fishing']['click_interval']['min'],
            self.config['fishing']['click_interval']['max']
        )
    
    def get_wait_times(self):
        """获取各状态等待时间"""
        return self.config['fishing']['wait_times']
    
    def get_key_press_duration(self):
        """获取按键操作时间"""
        return self.config['fishing']['key_press_duration']
    
    def get_click_slowdown_factor(self):
        """获取点击减速系数"""
        return self.config['fishing']['click_slowdown_factor']
    
    def get_hotkeys(self):
        """获取热键配置"""
        return self.config['hotkeys']
    
    def get_display_config(self):
        """获取显示配置"""
        return self.config['display']
    
    def get_ui_config(self):
        """获取UI配置"""
        return self.config['ui']
    
# 单例模式
_instance = None

def get_instance(config_path=None):
    """
    获取配置管理器单例
    
    Args:
        config_path: 配置文件路径，仅在首次调用时有效
    
    Returns:
        ConfigManager实例
    """
    global _instance
    if _instance is None:
        _instance = ConfigManager(config_path)
    return _instance 