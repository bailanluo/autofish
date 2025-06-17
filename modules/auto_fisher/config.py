#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AutoFish钓鱼脚本配置管理模块

负责管理钓鱼脚本的所有配置参数和设置。
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path


class FishingConfig:
    """钓鱼配置管理类"""
    
    def __init__(self):
        """初始化配置管理器"""
        # 获取项目根目录
        self.root_dir = Path(__file__).parent.parent.parent
        self.config_file = self.root_dir / "config" / "fishing_config.yaml"
        
        # 默认配置
        self.default_config = {
            # 模型配置
            "model": {
                "path": "runs/fishing_model_latest.pt",
                "confidence_threshold": 0.5,
                "detection_interval": 0.03,  # 默认检测间隔秒数
                # 动态检测间隔配置
                "dynamic_intervals": {
                    "idle": 0.1,           # 空闲状态 - 100ms
                    "waiting": 0.05,       # 等待上钩 - 50ms
                    "fish_hooked": 0.02,   # 鱼上钩 - 20ms (最快)
                    "pulling": 0.03,       # 提线中 - 30ms
                    "success": 0.1         # 成功状态 - 100ms
                }
            },
            
            # OCR配置
            "ocr": {
                "tesseract_path": "D:\\Python\\tool\\Tesseract-OCR",
                "language": "chi_sim+eng",
                "confidence_threshold": 60,
                "detection_interval": 0.05,  # OCR检测间隔秒数
                # 动态OCR检测间隔
                "dynamic_intervals": {
                    "pulling_normal": 0.03,     # 提线普通状态 - 30ms
                    "pulling_halfway": 0.02,    # 提线一半状态 - 20ms (最快)
                    "default": 0.05             # 默认 - 50ms
                }
            },
            
            # 状态映射
            "state_mapping": {
                0: "等待上钩状态",
                1: "鱼上钩末提线状态", 
                2: "提线中_耐力未到二分之一状态",
                3: "提线中_耐力已到二分之一状态",
                4: "向右拉_txt",
                5: "向左拉_txt",
                6: "钓鱼成功状态_txt"
            },
            
            # 钓鱼流程配置
            "fishing": {
                "max_wait_time": 180,  # 最大等待时间（秒）
                "click_interval_min": 0.054,  # 最小点击间隔
                "click_interval_max": 0.127,  # 最大点击间隔
                "pause_duration": 1.0,  # 暂停持续时间
                "success_wait_time": 1.5,  # 成功状态等待时间
                "cast_hold_time": 2.0  # 抛竿按住时间
            },
            
            # 快捷键配置
            "hotkeys": {
                "start": "F1",
                "stop": "F2",
                "pause": "F3"
            },
            
            # 界面配置
            "ui": {
                "show_status_window": True,
                "status_window_position": [10, 10],  # 状态窗口位置
                "status_window_alpha": 0.8  # 状态窗口透明度
            },
            
            # 按键映射
            "key_mapping": {
                "left_pull": "a",
                "right_pull": "f",
                "confirm": "f",
                "cast": "left_mouse"
            }
        }
        
        # 当前配置
        self.config = self.default_config.copy()
        
        # 加载配置文件
        self.load_config()
        
        logging.info("钓鱼配置管理器初始化完成")
    
    def load_config(self):
        """加载配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = yaml.safe_load(f)
                    if loaded_config:
                        self._merge_config(self.config, loaded_config)
                        logging.info(f"成功加载配置文件: {self.config_file}")
            else:
                # 创建默认配置文件
                self.save_config()
                logging.info(f"创建默认配置文件: {self.config_file}")
        except Exception as e:
            logging.error(f"加载配置文件失败: {e}")
    
    def save_config(self):
        """保存配置文件"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
            logging.info(f"配置文件保存成功: {self.config_file}")
        except Exception as e:
            logging.error(f"保存配置文件失败: {e}")
    
    def _merge_config(self, base: Dict, update: Dict):
        """递归合并配置"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def get(self, key_path: str, default=None):
        """
        获取配置值
        
        Args:
            key_path: 配置键路径，如 'model.path'
            default: 默认值
            
        Returns:
            配置值
        """
        try:
            keys = key_path.split('.')
            value = self.config
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any):
        """
        设置配置值
        
        Args:
            key_path: 配置键路径，如 'model.path'
            value: 配置值
        """
        try:
            keys = key_path.split('.')
            config = self.config
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]
            config[keys[-1]] = value
        except Exception as e:
            logging.error(f"设置配置值失败: {e}")
    
    def get_model_path(self) -> str:
        """获取模型文件路径"""
        model_path = self.get('model.path')
        if not os.path.isabs(model_path):
            model_path = self.root_dir / model_path
        return str(model_path)
    
    def get_tesseract_path(self) -> str:
        """获取Tesseract路径"""
        return self.get('ocr.tesseract_path')
    
    def get_state_name(self, state_id: int) -> str:
        """获取状态名称"""
        return self.get(f'state_mapping.{state_id}', f'未知状态{state_id}')
    
    def get_hotkeys(self) -> Dict[str, str]:
        """获取快捷键配置"""
        return self.get('hotkeys', {})
    
    def set_hotkey(self, action: str, key: str):
        """设置快捷键"""
        self.set(f'hotkeys.{action}', key)
        self.save_config()
    
    def get_detection_interval(self, state_type: str = "default") -> float:
        """
        获取检测间隔
        
        Args:
            state_type: 状态类型 ('idle', 'waiting', 'fish_hooked', 'pulling', 'success')
            
        Returns:
            检测间隔秒数
        """
        dynamic_intervals = self.get('model.dynamic_intervals', {})
        return dynamic_intervals.get(state_type, self.get('model.detection_interval', 0.03))
    
    def get_ocr_detection_interval(self, state_type: str = "default") -> float:
        """
        获取OCR检测间隔
        
        Args:
            state_type: 状态类型 ('pulling_normal', 'pulling_halfway', 'default')
            
        Returns:
            OCR检测间隔秒数
        """
        dynamic_intervals = self.get('ocr.dynamic_intervals', {})
        return dynamic_intervals.get(state_type, self.get('ocr.detection_interval', 0.05))


# 全局配置实例
_config_instance: Optional[FishingConfig] = None


def get_config() -> FishingConfig:
    """获取配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = FishingConfig()
    return _config_instance 