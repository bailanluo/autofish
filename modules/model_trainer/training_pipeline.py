"""
训练流程管理器 - 完整的端到端训练流程
负责整合数据处理、模型训练、结果保存等功能
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Callable

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from modules.logger import setup_logger, LogContext
from modules.model_trainer.data_processor import DataProcessor
from modules.model_trainer.yolo_trainer import YOLOTrainer

class TrainingPipeline:
    """完整的训练流程管理器"""
    
    def __init__(self, data_dir: str = "data", model_dir: str = "model", runs_dir: str = "runs"):
        """
        初始化训练流程管理器
        
        Args:
            data_dir: 数据目录
            model_dir: 预训练模型目录
            runs_dir: 训练结果保存目录
        """
        self.data_dir = Path(data_dir)
        self.model_dir = Path(model_dir)
        self.runs_dir = Path(runs_dir)
        self.logger = setup_logger('TrainingPipeline')
        
        # 初始化组件
        self.data_processor = DataProcessor(str(self.data_dir))
        self.yolo_trainer = YOLOTrainer(str(self.model_dir), str(self.data_dir), str(self.runs_dir))
        
        # 训练状态
        self.is_running = False
        self.current_stage = ""
        
        # 回调函数
        self.progress_callback: Optional[Callable] = None
        self.completion_callback: Optional[Callable] = None
        
        self.logger.info("训练流程管理器初始化完成")
        self.logger.info(f"数据目录: {self.data_dir}")
        self.logger.info(f"模型目录: {self.model_dir}")
        self.logger.info(f"结果目录: {self.runs_dir}")
    
    def set_progress_callback(self, callback: Callable[[str, Dict], None]):
        """
        设置进度回调函数
        
        Args:
            callback: 回调函数，接收阶段名称和进度数据
        """
        self.progress_callback = callback
        # 同时设置YOLO训练器的回调
        self.yolo_trainer.set_progress_callback(self._on_training_progress)
    
    def set_completion_callback(self, callback: Callable[[bool, str, Dict], None]):
        """
        设置完成回调函数
        
        Args:
            callback: 回调函数，接收成功标志、消息和结果数据
        """
        self.completion_callback = callback
        # 同时设置YOLO训练器的回调
        self.yolo_trainer.set_completion_callback(self._on_training_completion)
    
    def run_complete_training(self, config: Dict) -> bool:
        """
        运行完整的训练流程
        
        Args:
            config: 训练配置字典
            
        Returns:
            bool: 成功启动返回True
        """
        if self.is_running:
            self.logger.warning("训练流程已在运行中")
            return False
        
        try:
            self.is_running = True
            self.logger.info("=" * 60)
            self.logger.info("开始完整训练流程")
            self.logger.info("=" * 60)
            
            # 阶段1: 数据扫描和验证
            self._notify_progress("数据扫描", {"stage": 1, "total_stages": 4, "progress": 0})
            if not self._scan_and_validate_data():
                self._notify_completion(False, "数据扫描失败", {})
                return False
            
            # 阶段2: 数据预处理
            self._notify_progress("数据预处理", {"stage": 2, "total_stages": 4, "progress": 25})
            if not self._prepare_training_data(config):
                self._notify_completion(False, "数据预处理失败", {})
                return False
            
            # 阶段3: 模型训练
            self._notify_progress("模型训练", {"stage": 3, "total_stages": 4, "progress": 50})
            if not self._start_model_training(config):
                self._notify_completion(False, "模型训练启动失败", {})
                return False
            
            # 训练将在后台进行，完成后会调用回调函数
            return True
            
        except Exception as e:
            error_msg = f"训练流程启动失败: {str(e)}"
            self.logger.error(error_msg)
            self._notify_completion(False, error_msg, {})
            return False
        finally:
            if not self.yolo_trainer.is_training:
                self.is_running = False
    
    def stop_training(self):
        """停止训练流程"""
        if not self.is_running:
            return
        
        self.logger.info("正在停止训练流程...")
        self.yolo_trainer.stop_training()
        self.is_running = False
        self.logger.info("训练流程已停止")
    
    def get_training_status(self) -> Dict:
        """
        获取训练状态信息
        
        Returns:
            Dict: 状态信息
        """
        return {
            'is_running': self.is_running,
            'current_stage': self.current_stage,
            'yolo_training': self.yolo_trainer.is_training,
            'data_dir': str(self.data_dir),
            'model_dir': str(self.model_dir),
            'runs_dir': str(self.runs_dir)
        }
    
    def _scan_and_validate_data(self) -> bool:
        """扫描和验证数据"""
        try:
            self.current_stage = "数据扫描"
            self.logger.info("开始扫描训练数据...")
            
            # 检查数据目录
            images_dir = self.data_dir / "raw" / "images"
            if not images_dir.exists():
                self.logger.error(f"数据目录不存在: {images_dir}")
                self.logger.error(f"请确保数据位于 {images_dir} 目录下")
                return False
            
            # 扫描数据
            class_counts = self.data_processor.scan_data()
            if not class_counts:
                self.logger.error("未找到任何训练数据")
                return False
            
            # 验证数据质量
            total_images = sum(class_counts.values())
            valid_classes = sum(1 for count in class_counts.values() if count > 0)
            
            self.logger.info(f"数据扫描完成:")
            self.logger.info(f"  - 总类别数: {len(class_counts)}")
            self.logger.info(f"  - 有效类别: {valid_classes}")
            self.logger.info(f"  - 总图片数: {total_images}")
            
            # 检查数据是否足够
            if total_images < 10:
                self.logger.error("训练数据太少，至少需要10张图片")
                return False
            
            if valid_classes < 2:
                self.logger.error("有效类别太少，至少需要2个类别")
                return False
            
            # 显示详细统计
            for class_name, count in class_counts.items():
                if count > 0:
                    self.logger.info(f"  - {class_name}: {count} 张")
                else:
                    self.logger.warning(f"  - {class_name}: 0 张 (将被跳过)")
            
            return True
            
        except Exception as e:
            self.logger.error(f"数据扫描失败: {str(e)}")
            return False
    
    def _prepare_training_data(self, config: Dict) -> bool:
        """准备训练数据"""
        try:
            self.current_stage = "数据预处理"
            self.logger.info("开始准备训练数据...")
            
            # 获取数据分割比例
            train_ratio = config.get('train_ratio', 0.8)
            val_ratio = config.get('val_ratio', 0.2)
            force_recreate = config.get('force_recreate_data', False)
            
            self.logger.info(f"数据分割比例: 训练集 {train_ratio:.1%}, 验证集 {val_ratio:.1%}")
            
            # 准备检测数据
            success = self.data_processor.prepare_detection_data(
                train_ratio=train_ratio,
                val_ratio=val_ratio,
                force_recreate=force_recreate
            )
            
            if not success:
                self.logger.error("数据预处理失败")
                return False
            
            self.logger.info("数据预处理完成")
            return True
            
        except Exception as e:
            self.logger.error(f"数据预处理失败: {str(e)}")
            return False
    
    def _start_model_training(self, config: Dict) -> bool:
        """开始模型训练"""
        try:
            self.current_stage = "模型训练"
            self.logger.info("开始模型训练...")
            
            # 设置默认训练参数
            training_config = {
                'model_type': config.get('model_type', 'yolov8n'),
                'epochs': config.get('epochs', 100),
                'batch_size': config.get('batch_size', 16),
                'lr0': config.get('lr0', 0.01),
                'imgsz': config.get('imgsz', 640),
                'patience': config.get('patience', 50),
                'workers': config.get('workers', 8),
                'save_period': config.get('save_period', 10),
                
                # 高级参数
                'lrf': config.get('lrf', 0.01),
                'momentum': config.get('momentum', 0.937),
                'weight_decay': config.get('weight_decay', 0.0005),
                'warmup_epochs': config.get('warmup_epochs', 3),
                'cos_lr': config.get('cos_lr', False),
                'amp': config.get('amp', True),
                
                # 数据增强
                'hsv_h': config.get('hsv_h', 0.015),
                'hsv_s': config.get('hsv_s', 0.7),
                'hsv_v': config.get('hsv_v', 0.4),
                'fliplr': config.get('fliplr', 0.5),
                'mosaic': config.get('mosaic', 1.0),
                'mixup': config.get('mixup', 0.0),
                
                # 损失权重
                'box_loss_gain': config.get('box_loss_gain', 0.05),
                'cls_loss_gain': config.get('cls_loss_gain', 0.5),
                'dfl_loss_gain': config.get('dfl_loss_gain', 1.5),
            }
            
            self.logger.info("训练配置:")
            self.logger.info(f"  - 模型类型: {training_config['model_type']}")
            self.logger.info(f"  - 训练轮数: {training_config['epochs']}")
            self.logger.info(f"  - 批次大小: {training_config['batch_size']}")
            self.logger.info(f"  - 学习率: {training_config['lr0']}")
            self.logger.info(f"  - 图像尺寸: {training_config['imgsz']}")
            
            # 启动训练
            success = self.yolo_trainer.start_training(training_config)
            if not success:
                self.logger.error("模型训练启动失败")
                return False
            
            self.logger.info("模型训练已启动，将在后台进行...")
            return True
            
        except Exception as e:
            self.logger.error(f"模型训练启动失败: {str(e)}")
            return False
    
    def _on_training_progress(self, progress_data: Dict):
        """处理训练进度回调"""
        # 将训练进度转发给外部回调
        if self.progress_callback:
            try:
                # 添加阶段信息
                enhanced_progress = {
                    **progress_data,
                    'stage': 3,
                    'total_stages': 4,
                    'progress': 50 + (progress_data.get('progress', 0) * 0.4)  # 50-90%
                }
                self.progress_callback("模型训练", enhanced_progress)
            except Exception as e:
                self.logger.error(f"进度回调执行失败: {str(e)}")
    
    def _on_training_completion(self, success: bool, message: str):
        """处理训练完成回调"""
        try:
            self.current_stage = "训练完成"
            self.is_running = False
            
            if success:
                self.logger.info("=" * 60)
                self.logger.info("训练流程完成!")
                self.logger.info("=" * 60)
                
                # 收集训练结果信息
                result_data = self._collect_training_results()
                
                # 通知完成
                self._notify_progress("训练完成", {"stage": 4, "total_stages": 4, "progress": 100})
                self._notify_completion(True, "训练流程成功完成", result_data)
            else:
                self.logger.error(f"训练失败: {message}")
                self._notify_completion(False, f"训练失败: {message}", {})
                
        except Exception as e:
            self.logger.error(f"训练完成处理失败: {str(e)}")
            self._notify_completion(False, f"训练完成处理失败: {str(e)}", {})
    
    def _collect_training_results(self) -> Dict:
        """收集训练结果信息"""
        try:
            results = {
                'training_time': time.time(),
                'runs_dir': str(self.runs_dir),
                'trained_models': [],
                'training_dirs': []
            }
            
            # 查找训练结果目录
            train_dirs = list(self.runs_dir.glob("fishing_train_*"))
            if train_dirs:
                latest_train_dir = max(train_dirs, key=lambda x: x.stat().st_mtime)
                results['latest_training_dir'] = str(latest_train_dir)
                results['training_dirs'] = [str(d) for d in train_dirs]
                
                # 查找模型文件
                weights_dir = latest_train_dir / "weights"
                if weights_dir.exists():
                    model_files = list(weights_dir.glob("*.pt"))
                    results['model_files'] = [str(f) for f in model_files]
            
            # 查找保存的模型
            model_files = list(self.runs_dir.glob("fishing_model_*.pt"))
            results['trained_models'] = [str(f) for f in model_files]
            
            return results
            
        except Exception as e:
            self.logger.error(f"收集训练结果失败: {str(e)}")
            return {}
    
    def _notify_progress(self, stage: str, progress_data: Dict):
        """通知进度更新"""
        if self.progress_callback:
            try:
                self.progress_callback(stage, progress_data)
            except Exception as e:
                self.logger.error(f"进度通知失败: {str(e)}")
    
    def _notify_completion(self, success: bool, message: str, result_data: Dict):
        """通知训练完成"""
        if self.completion_callback:
            try:
                self.completion_callback(success, message, result_data)
            except Exception as e:
                self.logger.error(f"完成通知失败: {str(e)}")

if __name__ == "__main__":
    # 测试训练流程
    def progress_callback(stage: str, data: Dict):
        print(f"[{stage}] 进度: {data}")
    
    def completion_callback(success: bool, message: str, data: Dict):
        print(f"训练完成: {'成功' if success else '失败'}")
        print(f"消息: {message}")
        print(f"结果: {data}")
    
    # 创建训练流程
    pipeline = TrainingPipeline()
    pipeline.set_progress_callback(progress_callback)
    pipeline.set_completion_callback(completion_callback)
    
    # 测试配置
    config = {
        'model_type': 'yolov8n',
        'epochs': 10,
        'batch_size': 8,
        'lr0': 0.01,
        'train_ratio': 0.8,
        'val_ratio': 0.2
    }
    
    # 运行训练
    success = pipeline.run_complete_training(config)
    print(f"训练启动: {'成功' if success else '失败'}") 