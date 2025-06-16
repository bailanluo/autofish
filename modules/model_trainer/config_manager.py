"""
模型训练配置管理器
负责加载和管理训练配置、帮助文本等
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class TrainingConfigManager:
    """训练配置管理器"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录，默认为当前模块目录
        """
        if config_dir is None:
            config_dir = Path(__file__).parent
        
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "config.yaml"
        self.help_file = self.config_dir / "help_texts.yaml"
        
        # 加载配置
        self.config = self._load_config()
        self.help_texts = self._load_help_texts()
        
    def _load_config(self) -> Dict[str, Any]:
        """加载训练配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                logger.info(f"配置文件加载成功: {self.config_file}")
                return config
            else:
                logger.warning(f"配置文件不存在: {self.config_file}")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            return self._get_default_config()
    
    def _load_help_texts(self) -> Dict[str, str]:
        """加载帮助文本"""
        try:
            if self.help_file.exists():
                with open(self.help_file, 'r', encoding='utf-8') as f:
                    help_texts = yaml.safe_load(f)
                logger.info(f"帮助文本加载成功: {self.help_file}")
                return help_texts
            else:
                logger.warning(f"帮助文本文件不存在: {self.help_file}")
                return {}
        except Exception as e:
            logger.error(f"加载帮助文本失败: {str(e)}")
            return {}
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'models': {
                'detection': {
                    'yolov8s': {
                        'name': 'YOLOv8 Small',
                        'description': '中等检测模型，推荐用于钓鱼检测',
                        'epochs': 150,
                        'batch_size': 16,
                        'learning_rate': 0.01,
                        'image_size': 640,
                        'patience': 50,
                        'save_period': 10
                    }
                }
            },
            'training': {
                'k_fold': {
                    'default_folds': 5,
                    'min_folds': 3,
                    'max_folds': 10
                }
            },
            'data': {
                'classes': {
                    0: 'fishing_success_txt',
                    1: 'pull_right_txt',
                    2: 'hooked_no_pull',
                    3: 'has_bait',
                    4: 'select_bait',
                    5: 'pull_left_txt',
                    6: 'not_fishing',
                    7: 'pulling_stamina_half',
                    8: 'pulling_stamina_low',
                    9: 'in_fishing',
                    10: 'waiting_hook'
                }
            }
        }
    
    def get_model_config(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        获取指定模型的配置
        
        Args:
            model_name: 模型名称（如 yolov8s）
            
        Returns:
            模型配置字典，如果不存在返回None
        """
        # 提取实际模型名称
        actual_model = model_name.split(' ')[0].lower()
        
        # 判断是检测还是分类模型
        if '-cls' in actual_model:
            model_type = 'classification'
        else:
            model_type = 'detection'
        
        models = self.config.get('models', {}).get(model_type, {})
        return models.get(actual_model)
    
    def get_available_models(self) -> List[str]:
        """获取可用的模型列表"""
        models = []
        
        # 检测模型
        detection_models = self.config.get('models', {}).get('detection', {})
        for model_key, model_config in detection_models.items():
            name = model_config.get('name', model_key)
            description = model_config.get('description', '')
            models.append(f"{model_key} ({description})")
        
        # 分类模型
        classification_models = self.config.get('models', {}).get('classification', {})
        for model_key, model_config in classification_models.items():
            name = model_config.get('name', model_key)
            description = model_config.get('description', '')
            models.append(f"{model_key} ({description})")
        
        return models
    
    def get_default_training_params(self, model_name: str) -> Dict[str, Any]:
        """
        获取模型的默认训练参数
        
        Args:
            model_name: 模型名称
            
        Returns:
            默认训练参数字典
        """
        model_config = self.get_model_config(model_name)
        if model_config:
            return {
                'epochs': model_config.get('epochs', 100),
                'batch_size': model_config.get('batch_size', 16),
                'learning_rate': model_config.get('learning_rate', 0.01),
                'image_size': model_config.get('image_size', 640),
                'patience': model_config.get('patience', 50),
                'save_period': model_config.get('save_period', 10)
            }
        else:
            # 返回通用默认值
            return {
                'epochs': 100,
                'batch_size': 16,
                'learning_rate': 0.01,
                'image_size': 640,
                'patience': 50,
                'save_period': 10
            }
    
    def get_k_fold_config(self) -> Dict[str, int]:
        """获取K折交叉验证配置"""
        k_fold_config = self.config.get('training', {}).get('k_fold', {})
        return {
            'default_folds': k_fold_config.get('default_folds', 5),
            'min_folds': k_fold_config.get('min_folds', 3),
            'max_folds': k_fold_config.get('max_folds', 10)
        }
    
    def get_image_size_options(self) -> List[int]:
        """获取图片尺寸选项"""
        return self.config.get('inference', {}).get('image_sizes', [320, 416, 512, 640, 800, 1024, 1280])
    
    def get_class_names(self) -> Dict[int, str]:
        """获取类别名称映射"""
        return self.config.get('data', {}).get('classes', {})
    
    def get_chinese_names(self) -> Dict[int, str]:
        """获取中文类别名称映射"""
        return self.config.get('data', {}).get('chinese_names', {})
    
    def get_help_text(self, help_key: str) -> str:
        """
        获取帮助文本
        
        Args:
            help_key: 帮助文本键名
            
        Returns:
            帮助文本内容
        """
        return self.help_texts.get(help_key, f"帮助文本 '{help_key}' 未找到")
    
    def get_validation_config(self) -> Dict[str, Any]:
        """获取验证配置"""
        return self.config.get('validation', {})
    
    def get_training_config(self) -> Dict[str, Any]:
        """获取训练策略配置"""
        return self.config.get('training', {})
    
    def get_hardware_config(self) -> Dict[str, Any]:
        """获取硬件配置"""
        return self.config.get('hardware', {})
    
    def get_output_config(self) -> Dict[str, Any]:
        """获取输出配置"""
        return self.config.get('output', {})
    
    def update_config(self, key_path: str, value: Any) -> bool:
        """
        更新配置值
        
        Args:
            key_path: 配置键路径，用点分隔（如 'models.detection.yolov8s.epochs'）
            value: 新值
            
        Returns:
            更新成功返回True
        """
        try:
            keys = key_path.split('.')
            config = self.config
            
            # 导航到目标位置
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]
            
            # 设置值
            config[keys[-1]] = value
            
            # 保存配置
            return self.save_config()
            
        except Exception as e:
            logger.error(f"更新配置失败: {str(e)}")
            return False
    
    def save_config(self) -> bool:
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"配置已保存: {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"保存配置失败: {str(e)}")
            return False
    
    def validate_training_params(self, params: Dict[str, Any]) -> Dict[str, str]:
        """
        验证训练参数
        
        Args:
            params: 训练参数字典
            
        Returns:
            验证错误字典，空字典表示验证通过
        """
        errors = {}
        
        # 验证epochs
        epochs = params.get('epochs', 0)
        if not isinstance(epochs, int) or epochs <= 0:
            errors['epochs'] = "训练轮数必须是正整数"
        elif epochs > 1000:
            errors['epochs'] = "训练轮数不建议超过1000"
        
        # 验证batch_size
        batch_size = params.get('batch_size', 0)
        if not isinstance(batch_size, int) or batch_size <= 0:
            errors['batch_size'] = "批次大小必须是正整数"
        elif batch_size > 64:
            errors['batch_size'] = "批次大小过大可能导致内存不足"
        
        # 验证learning_rate
        lr = params.get('learning_rate', 0)
        if not isinstance(lr, (int, float)) or lr <= 0:
            errors['learning_rate'] = "学习率必须是正数"
        elif lr > 1.0:
            errors['learning_rate'] = "学习率过大可能导致训练不稳定"
        
        # 验证image_size
        image_size = params.get('image_size', 0)
        valid_sizes = self.get_image_size_options()
        if image_size not in valid_sizes:
            errors['image_size'] = f"图片尺寸必须是以下值之一: {valid_sizes}"
        
        return errors 