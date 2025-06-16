"""
数据采集工具配置管理器
独立的配置管理，不依赖主项目配置
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any


class DataCollectorConfig:
    """数据采集工具配置管理器"""
    
    def __init__(self, config_path: str = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，默认为当前目录下的config.yaml
        """
        if config_path is None:
            # 使用当前文件所在目录的config.yaml
            current_dir = Path(__file__).parent
            config_path = current_dir / "config.yaml"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                return config if config else {}
            else:
                # 如果配置文件不存在，返回默认配置
                return self._get_default_config()
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'data_collection': {
                'image_format': 'png',
                'image_quality': 95,
                'data_dir': 'data',
                'max_images_per_category': 1000
            },
            'hotkeys': {
                'select_region': 'ctrl+alt+y',
                'quick_capture': 'y',
                'pause_capture': 'ctrl+alt+p'
            },
            'ui': {
                'window_title': '通用图像数据采集工具',
                'window_size': '800x600',
                'preview_size': 200
            },
            'system': {
                'run_as_admin': True,  # 默认以管理员身份启动
                'auto_save_hotkeys': True  # 自动保存热键设置
            },
            'logging': {
                'level': 'INFO',
                'file': 'data_collector.log'
            }
        }
    
    def save_config(self):
        """保存配置到文件"""
        try:
            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def get(self, key: str, default=None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键，如 'hotkeys.select_region'
            default: 默认值
            
        Returns:
            配置值或默认值
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """
        设置配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
        """
        keys = key.split('.')
        config = self.config
        
        # 导航到最后一级的父级
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置最后一级的值
        config[keys[-1]] = value
    
    def get_hotkeys(self) -> Dict[str, str]:
        """获取热键配置"""
        return self.config.get('hotkeys', {
            'select_region': 'ctrl+alt+y',
            'quick_capture': 'y',
            'pause_capture': 'ctrl+alt+p'
        })
    
    def set_hotkeys(self, hotkeys: Dict[str, str]):
        """设置热键配置"""
        if 'hotkeys' not in self.config:
            self.config['hotkeys'] = {}
        self.config['hotkeys'].update(hotkeys)
    
    def get_data_dir(self) -> str:
        """获取数据保存目录"""
        return self.get('data_collection.data_dir', 'data')
    
    def get_image_format(self) -> str:
        """获取图像格式"""
        return self.get('data_collection.image_format', 'png')
    
    def get_image_quality(self) -> int:
        """获取图像质量"""
        return self.get('data_collection.image_quality', 95)
    
    def get_max_images_per_category(self) -> int:
        """获取每类别最大图像数"""
        return self.get('data_collection.max_images_per_category', 1000)
    
    def get_preview_size(self) -> int:
        """获取预览图像大小"""
        return self.get('ui.preview_size', 200)
    
    def get_window_title(self) -> str:
        """获取窗口标题"""
        return self.get('ui.window_title', '通用图像数据采集工具')
    
    def get_window_size(self) -> str:
        """获取窗口大小"""
        return self.get('ui.window_size', '800x600')
    
    def get_run_as_admin(self) -> bool:
        """获取是否以管理员身份启动"""
        return self.get('system.run_as_admin', True)
    
    def set_run_as_admin(self, value: bool):
        """设置是否以管理员身份启动"""
        self.set('system.run_as_admin', value)
    
    def get_auto_save_hotkeys(self) -> bool:
        """获取是否自动保存热键设置"""
        return self.get('system.auto_save_hotkeys', True)
    
    def set_auto_save_hotkeys(self, value: bool):
        """设置是否自动保存热键设置"""
        self.set('system.auto_save_hotkeys', value) 