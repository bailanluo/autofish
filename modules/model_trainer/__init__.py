"""
AutoFish 模型训练模块 v2.2

这个模块提供完整的YOLO模型训练功能，包括：
- 数据预处理和管理
- YOLO模型训练和验证
- OCR特征提取和融合
- 训练进度监控界面
- 桌面测试工具

主要组件：
- DataProcessor: 数据预处理和增强
- YOLOTrainer: YOLO模型训练管理
- OCRFeatureExtractor: OCR文本特征提取
- HybridTrainer: 图像+文本混合训练
- TrainingMonitor: 训练进度监控界面
- ModelValidator: 模型验证和评估
- DesktopTester: 桌面实时测试工具
"""

__version__ = "2.2.0"
__author__ = "AutoFish Team"

# 导入主要类
try:
    from .data_processor import DataProcessor
    from .yolo_trainer import YOLOTrainer
    from .training_monitor import TrainingMonitorApp
    from .model_validator import ModelValidator
    from .desktop_tester import DesktopTesterApp
    
    __all__ = [
        'DataProcessor',
        'YOLOTrainer', 
        'TrainingMonitorApp',
        'ModelValidator',
        'DesktopTesterApp'
    ]
except ImportError as e:
    # 如果某些依赖不可用，只导入可用的组件
    print(f"警告：部分模型训练组件不可用: {e}")
    __all__ = [] 