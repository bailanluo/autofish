"""
YOLO训练管理器
负责YOLO模型的训练、验证和管理
"""

import os
import sys
import time
import threading
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Callable
import yaml

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from modules.logger import setup_logger, LogContext

try:
    from ultralytics import YOLO
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False

class YOLOTrainer:
    """YOLO训练管理器 - 负责模型训练和验证"""
    
    def __init__(self, model_dir: str = "model", data_dir: str = "data", runs_dir: str = "runs"):
        """
        初始化YOLO训练器
        
        Args:
            model_dir: 预训练模型文件目录
            data_dir: 训练数据目录
            runs_dir: 训练结果保存目录
        """
        self.model_dir = Path(model_dir)
        self.data_dir = Path(data_dir)
        self.runs_dir = Path(runs_dir)
        self.logger = setup_logger('YOLOTrainer')
        
        # 检查依赖
        if not ULTRALYTICS_AVAILABLE:
            self.logger.error("Ultralytics YOLO库未安装，请执行: pip install ultralytics")
            raise ImportError("需要安装ultralytics库")
        
        # 训练状态
        self.is_training = False
        self.current_model = None
        self.training_thread = None
        
        # 回调函数
        self.progress_callback: Optional[Callable] = None
        self.completion_callback: Optional[Callable] = None
        
        # 确保目录存在
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        
        # 检测最佳设备
        self.device = self._detect_best_device()
        self.logger.info(f"使用设备: {self.device}")
        self.logger.info(f"预训练模型目录: {self.model_dir}")
        self.logger.info(f"训练结果保存目录: {self.runs_dir}")
    
    def _detect_best_device(self) -> str:
        """检测最佳训练设备"""
        try:
            import torch
            if torch.cuda.is_available():
                device_count = torch.cuda.device_count()
                self.logger.info(f"检测到 {device_count} 个CUDA设备")
                return '0'  # 使用第一个GPU
            else:
                self.logger.info("未检测到CUDA设备，使用CPU")
                return 'cpu'
        except ImportError:
            self.logger.warning("PyTorch未安装，使用CPU")
            return 'cpu'
        except Exception as e:
            self.logger.warning(f"设备检测失败: {str(e)}，使用CPU")
            return 'cpu'
    
    def set_progress_callback(self, callback: Callable[[Dict], None]):
        """
        设置训练进度回调函数
        
        Args:
            callback: 回调函数，接收训练进度字典
        """
        self.progress_callback = callback
    
    def set_completion_callback(self, callback: Callable[[bool, str], None]):
        """
        设置训练完成回调函数
        
        Args:
            callback: 回调函数，接收成功标志和结果信息
        """
        self.completion_callback = callback
    
    def start_training(self, config: Dict) -> bool:
        """
        开始训练模型
        
        Args:
            config: 训练配置字典
            
        Returns:
            bool: 成功启动返回True，否则返回False
        """
        if self.is_training:
            self.logger.warning("训练已在进行中，无法重复启动")
            return False
        
        try:
            # 验证配置
            if not self._validate_config(config):
                return False
            
            # 启动训练线程
            self.training_thread = threading.Thread(
                target=self._train_model_thread,
                args=(config,),
                daemon=True
            )
            self.training_thread.start()
            
            self.is_training = True
            self.logger.info("YOLO训练已启动")
            return True
            
        except Exception as e:
            self.logger.error(f"启动训练失败: {str(e)}")
            return False
    
    def stop_training(self):
        """停止训练"""
        if not self.is_training:
            return
        
        self.is_training = False
        self.logger.info("正在停止训练...")
        
        # 等待训练线程结束
        if self.training_thread and self.training_thread.is_alive():
            self.training_thread.join(timeout=10)
        
        self.logger.info("训练已停止")
    
    def _validate_config(self, config: Dict) -> bool:
        """
        验证训练配置
        
        Args:
            config: 训练配置
            
        Returns:
            bool: 配置有效返回True
        """
        required_keys = ['model_type', 'epochs', 'batch_size', 'lr0']
        
        for key in required_keys:
            if key not in config:
                self.logger.error(f"训练配置缺少必要参数: {key}")
                return False
        
        # 检查数据配置文件
        data_config_path = self.data_dir / "train_config.yaml"
        if not data_config_path.exists():
            self.logger.error(f"训练数据配置文件不存在: {data_config_path}")
            return False
        
        return True
    
    def _train_model_thread(self, config: Dict):
        """
        训练模型的线程函数
        
        Args:
            config: 训练配置
        """
        try:
            with LogContext(self.logger, "YOLO模型训练"):
                # 1. 初始化模型
                model = self._initialize_model(config['model_type'])
                if not model:
                    self._notify_completion(False, "模型初始化失败")
                    return
                
                self.current_model = model
                
                # 2. 设置训练参数
                train_args = self._prepare_train_args(config)
                
                # 3. 设置训练回调
                self._setup_training_callbacks(model, config)
                
                # 4. 开始训练
                self.logger.info(f"开始训练 {config['model_type']} 模型...")
                self._notify_progress({
                    'status': 'training',
                    'epoch': 0,
                    'total_epochs': config['epochs'],
                    'progress': 0.0,
                    'metrics': {}
                })
                
                # 执行训练
                results = model.train(**train_args)
                
                # 5. 保存训练好的模型
                saved_model_path = self._save_trained_model(model, config)
                
                # 6. 训练完成
                message = f"训练成功完成! 模型保存至: {saved_model_path}"
                self.logger.info(message)
                self._notify_completion(True, message)
                
        except Exception as e:
            error_msg = f"训练失败: {str(e)}"
            self.logger.error(error_msg)
            self._notify_completion(False, error_msg)
        finally:
            self.is_training = False
    
    def _initialize_model(self, model_type: str) -> Optional[object]:
        """
        初始化YOLO模型
        
        Args:
            model_type: 模型类型 (如 'yolov8n', 'yolo11n')
            
        Returns:
            YOLO模型实例或None
        """
        try:
            model_file = f"{model_type}.pt"
            model_path = self.model_dir / model_file
            
            self.logger.info(f"初始化模型: {model_type}")
            
            # 检查本地是否存在预训练模型
            if model_path.exists():
                self.logger.info(f"使用本地模型: {model_path}")
                model = YOLO(str(model_path))
            else:
                self.logger.info(f"本地模型不存在，将下载: {model_file}")
                
                # 在临时目录中下载模型
                import tempfile
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    original_cwd = os.getcwd()
                    
                    try:
                        # 切换到临时目录进行下载
                        os.chdir(temp_path)
                        self.logger.info(f"正在下载模型: {model_file}")
                        
                        # 在临时目录中初始化模型（这会触发下载）
                        model = YOLO(model_file)
                        
                        # 查找下载的模型文件
                        downloaded_files = []
                        
                        # 检查临时目录中的模型文件
                        for pattern in ['*.pt', '**/*.pt']:
                            downloaded_files.extend(list(temp_path.glob(pattern)))
                        
                        # 检查当前工作目录（可能下载到这里）
                        current_dir = Path.cwd()
                        for pattern in ['*.pt']:
                            downloaded_files.extend(list(current_dir.glob(pattern)))
                        
                        # 移动下载的文件到model目录
                        for downloaded_file in downloaded_files:
                            if downloaded_file.name == model_file:
                                target_path = self.model_dir / model_file
                                if not target_path.exists():
                                    shutil.copy2(str(downloaded_file), str(target_path))
                                    self.logger.info(f"模型已下载到: {target_path}")
                                break
                        
                        # 验证模型文件是否存在
                        if not model_path.exists():
                            # 如果还是没有，尝试从用户缓存目录复制
                            import platform
                            if platform.system() == "Windows":
                                cache_dir = Path.home() / ".cache" / "ultralytics"
                            else:
                                cache_dir = Path.home() / ".cache" / "ultralytics"
                            
                            cache_model = cache_dir / model_file
                            if cache_model.exists():
                                shutil.copy2(str(cache_model), str(model_path))
                                self.logger.info(f"从缓存复制模型到: {model_path}")
                
                    finally:
                        # 恢复工作目录
                        os.chdir(original_cwd)
                        
                        # 清理根目录可能下载的文件
                        root_model = Path(original_cwd) / model_file
                        if root_model.exists() and not model_path.exists():
                            shutil.move(str(root_model), str(model_path))
                            self.logger.info(f"移动模型文件: {model_file} -> model/")
                        elif root_model.exists() and model_path.exists():
                            root_model.unlink()  # 删除重复文件
                            self.logger.info(f"删除重复的根目录模型文件: {model_file}")
                
                # 重新加载模型（使用正确路径的模型文件）
                if model_path.exists():
                    model = YOLO(str(model_path))
                
                # 验证模型文件是否存在
                if not model_path.exists():
                    self.logger.warning(f"模型文件下载后未找到: {model_path}")
                    # 尝试从其他可能的位置复制
                    try:
                        # 检查当前目录
                        current_model = Path(model_file)
                        if current_model.exists():
                            shutil.move(str(current_model), str(model_path))
                            self.logger.info(f"模型已移动到: {model_path}")
                        else:
                            # 检查用户缓存目录
                            home_dir = Path.home()
                            cache_path = home_dir / ".cache" / "ultralytics" / model_file
                            if cache_path.exists():
                                shutil.copy2(cache_path, model_path)
                                self.logger.info(f"模型已从缓存复制到: {model_path}")
                    except Exception as copy_error:
                        self.logger.warning(f"复制模型文件失败: {copy_error}")
            
            self.logger.info(f"模型初始化成功: {model_type}")
            return model
            
        except Exception as e:
            self.logger.error(f"模型初始化失败: {str(e)}")
            return None
    
    def _prepare_train_args(self, config: Dict) -> Dict:
        """
        准备完整的训练参数，包含高级训练策略
        
        Args:
            config: 训练配置
            
        Returns:
            Dict: 训练参数字典
        """
        # 数据配置文件路径
        data_config = self.data_dir / "train_config.yaml"
        if not data_config.exists():
            # 如果主配置文件不存在，尝试使用备用配置文件
            data_config = self.data_dir / "train_simple.yaml"
            if not data_config.exists():
                raise FileNotFoundError(f"训练配置文件不存在: train_config.yaml 或 train_simple.yaml")
        
        # 创建训练时间戳
        timestamp = int(time.time())
        training_name = f"fishing_train_{timestamp}"
        
        # 完整的训练参数配置
        train_args = {
            # 基础参数
            'data': str(data_config),
            'epochs': config.get('epochs', 100),
            'batch': config.get('batch_size', 16),
            'imgsz': config.get('imgsz', 640),
            'device': self.device,
            'workers': config.get('workers', 8),
            
            # 保存设置 - 保存到runs目录
            'project': str(self.runs_dir),
            'name': training_name,
            'save': True,
            'save_period': config.get('save_period', 10),
            
            # 学习率和优化器设置
            'lr0': config.get('lr0', 0.01),           # 初始学习率
            'lrf': config.get('lrf', 0.01),           # 最终学习率 (lr0 * lrf)
            'momentum': config.get('momentum', 0.937), # SGD动量
            'weight_decay': config.get('weight_decay', 0.0005), # 权重衰减
            'warmup_epochs': config.get('warmup_epochs', 3),    # 预热轮数
            'warmup_momentum': config.get('warmup_momentum', 0.8), # 预热动量
            'warmup_bias_lr': config.get('warmup_bias_lr', 0.1),   # 预热偏置学习率
            
            # 早停和验证设置
            'patience': config.get('patience', 50),    # 早停耐心值
            'val': True,                               # 启用验证
            'plots': True,                             # 生成训练图表
            'save_json': True,                         # 保存JSON结果
            
            # 数据增强参数
            'hsv_h': config.get('hsv_h', 0.015),      # 色调增强
            'hsv_s': config.get('hsv_s', 0.7),        # 饱和度增强
            'hsv_v': config.get('hsv_v', 0.4),        # 明度增强
            'degrees': config.get('degrees', 0.0),     # 旋转角度
            'translate': config.get('translate', 0.1), # 平移
            'scale': config.get('scale', 0.5),         # 缩放
            'shear': config.get('shear', 0.0),         # 剪切
            'perspective': config.get('perspective', 0.0), # 透视变换
            'flipud': config.get('flipud', 0.0),       # 上下翻转概率
            'fliplr': config.get('fliplr', 0.5),       # 左右翻转概率
            'mosaic': config.get('mosaic', 1.0),       # 马赛克增强概率
            'mixup': config.get('mixup', 0.0),         # 混合增强概率
            'copy_paste': config.get('copy_paste', 0.0), # 复制粘贴增强
            
            # 损失函数权重
            'box': config.get('box_loss_gain', 0.05),  # 边界框损失权重
            'cls': config.get('cls_loss_gain', 0.5),   # 分类损失权重
            'dfl': config.get('dfl_loss_gain', 1.5),   # DFL损失权重
            
            # 其他设置
            'cache': False,                            # 关闭缓存避免内存问题
            'rect': False,                             # 矩形训练
            'cos_lr': config.get('cos_lr', False),     # 余弦学习率调度
            'close_mosaic': config.get('close_mosaic', 10), # 最后N轮关闭马赛克
            'resume': config.get('resume', False),     # 恢复训练
            'amp': config.get('amp', True),            # 自动混合精度
            'fraction': config.get('fraction', 1.0),   # 数据集使用比例
            'profile': config.get('profile', False),   # 性能分析
            'freeze': config.get('freeze', None),      # 冻结层数
            'multi_scale': config.get('multi_scale', False), # 多尺度训练
            'overlap_mask': config.get('overlap_mask', True), # 重叠掩码
            'mask_ratio': config.get('mask_ratio', 4), # 掩码下采样比例
            'dropout': config.get('dropout', 0.0),     # Dropout概率
        }
        
        self.logger.info("训练参数配置:")
        self.logger.info(f"  数据配置: {data_config}")
        self.logger.info(f"  训练轮数: {train_args['epochs']}")
        self.logger.info(f"  批次大小: {train_args['batch']}")
        self.logger.info(f"  图像尺寸: {train_args['imgsz']}")
        self.logger.info(f"  初始学习率: {train_args['lr0']}")
        self.logger.info(f"  早停耐心值: {train_args['patience']}")
        self.logger.info(f"  结果保存到: {self.runs_dir / training_name}")
        
        return train_args
    
    def _setup_training_callbacks(self, model: object, config: Dict):
        """
        设置训练回调函数，监控训练进度
        
        Args:
            model: YOLO模型实例
            config: 训练配置
        """
        try:
            # 添加训练回调
            def on_train_epoch_end(trainer):
                """训练轮次结束回调"""
                try:
                    # 获取epoch信息
                    epoch = 0
                    epochs = 100  # 默认值
                    
                    # 获取总轮数
                    if hasattr(trainer, 'args') and hasattr(trainer.args, 'epochs'):
                        epochs = trainer.args.epochs
                    
                    # 获取当前epoch
                    if hasattr(trainer, 'epoch') and trainer.epoch is not None:
                        epoch = trainer.epoch
                    elif hasattr(trainer, 'current_epoch') and trainer.current_epoch is not None:
                        epoch = trainer.current_epoch
                    
                    # 计算进度
                    if epoch > 0 and epochs > 0:
                        progress = ((epoch + 1) / epochs) * 100
                        # 只在有效epoch时记录日志
                        self.logger.info(f"轮次 {epoch + 1}/{epochs} 训练完成")
                    else:
                        progress = 0
                        # 简化的日志输出
                        self.logger.debug(f"训练轮次完成")
                    
                    # 通知UI更新进度
                    self._notify_progress({
                        'status': 'training',
                        'epoch': max(1, epoch + 1),
                        'total_epochs': epochs,
                        'progress': progress,
                        'metrics': {}  # 训练阶段不传递验证指标
                    })
                    
                except Exception as e:
                    self.logger.debug(f"训练回调失败: {str(e)}")
            
            def on_val_end(trainer):
                """验证结束回调 - 修复epoch获取问题"""
                try:
                    # YOLO训练器属性获取
                    epoch = 0
                    epochs = 100  # 默认值
                    
                    # 获取总轮数
                    if hasattr(trainer, 'args') and hasattr(trainer.args, 'epochs'):
                        epochs = trainer.args.epochs
                    
                    # 获取当前epoch - YOLO通常使用这些属性
                    if hasattr(trainer, 'epoch') and trainer.epoch is not None:
                        epoch = trainer.epoch
                    elif hasattr(trainer, 'current_epoch') and trainer.current_epoch is not None:
                        epoch = trainer.current_epoch
                    
                    # 如果还是获取不到epoch，可能是YOLO版本差异
                    # 我们可以从训练输出中推断当前进度
                    if epoch == 0 and hasattr(trainer, 'args'):
                        # 在无法获取精确epoch的情况下，减少日志噪音
                        self.logger.debug(f"验证完成 (训练进行中)")
                    else:
                        # 正常情况下显示详细信息
                        self.logger.info(f"轮次 {epoch + 1}/{epochs} 验证完成")
                    
                    # 获取训练指标
                    metrics = {}
                    
                    # 尝试获取验证指标
                    if hasattr(trainer, 'metrics') and trainer.metrics:
                        try:
                            metrics_obj = trainer.metrics
                            
                            # 获取基本的检测指标
                            if hasattr(metrics_obj, 'box'):
                                box_metrics = metrics_obj.box
                                if hasattr(box_metrics, 'map50'):
                                    metrics['map50'] = float(box_metrics.map50)
                                if hasattr(box_metrics, 'map'):
                                    metrics['map50_95'] = float(box_metrics.map)
                                if hasattr(box_metrics, 'mp'):
                                    metrics['precision'] = float(box_metrics.mp)
                                if hasattr(box_metrics, 'mr'):
                                    metrics['recall'] = float(box_metrics.mr)
                            
                        except Exception:
                            # 如果指标获取失败，使用空字典
                            metrics = {}
                    
                    # 计算进度百分比
                    if epoch > 0 and epochs > 0:
                        progress = ((epoch + 1) / epochs) * 100
                    else:
                        progress = 0
                    
                    # 通知UI更新进度
                    self._notify_progress({
                        'status': 'validation',
                        'epoch': max(1, epoch + 1),  # 确保至少显示1
                        'total_epochs': epochs,
                        'progress': progress,
                        'metrics': metrics
                    })
                        
                except Exception as e:
                    # 简化错误处理
                    self.logger.debug(f"验证回调失败: {str(e)}")
            
            # 注册回调函数
            if hasattr(model, 'add_callback'):
                model.add_callback('on_train_epoch_end', on_train_epoch_end)
                model.add_callback('on_val_end', on_val_end)
                self.logger.info("训练回调函数已注册")
            else:
                self.logger.warning("模型不支持回调函数")
                
        except Exception as e:
            self.logger.error(f"设置训练回调失败: {str(e)}")
    
    def _save_trained_model(self, model: object, config: Dict) -> str:
        """
        保存训练好的模型到runs目录
        
        Args:
            model: 训练好的模型
            config: 训练配置
            
        Returns:
            str: 保存的模型文件路径
        """
        try:
            # YOLO训练完成后，模型已经自动保存到runs目录中
            # 我们需要找到最新的训练结果目录
            
            # 查找最新的训练目录
            train_dirs = list(self.runs_dir.glob("fishing_train_*"))
            if not train_dirs:
                self.logger.error("未找到训练结果目录")
                return ""
            
            # 按时间排序，获取最新的
            latest_train_dir = max(train_dirs, key=lambda x: x.stat().st_mtime)
            weights_dir = latest_train_dir / "weights"
            
            if not weights_dir.exists():
                self.logger.error(f"权重目录不存在: {weights_dir}")
                return ""
            
            # 查找最佳模型文件
            best_model = weights_dir / "best.pt"
            last_model = weights_dir / "last.pt"
            
            if best_model.exists():
                model_path = best_model
                self.logger.info(f"找到最佳模型: {model_path}")
            elif last_model.exists():
                model_path = last_model
                self.logger.info(f"使用最后模型: {model_path}")
            else:
                self.logger.error("未找到训练好的模型文件")
                return ""
            
            # 创建一个带时间戳的副本到runs根目录
            timestamp = int(time.time())
            final_model_name = f"fishing_model_{timestamp}.pt"
            final_model_path = self.runs_dir / final_model_name
            
            shutil.copy2(model_path, final_model_path)
            
            # 同时创建一个最新模型的链接
            latest_model_path = self.runs_dir / "fishing_model_latest.pt"
            if latest_model_path.exists():
                latest_model_path.unlink()
            shutil.copy2(model_path, latest_model_path)
            
            self.logger.info("=" * 50)
            self.logger.info("模型保存完成!")
            self.logger.info(f"训练目录: {latest_train_dir}")
            self.logger.info(f"最佳模型: {model_path}")
            self.logger.info(f"副本保存: {final_model_path}")
            self.logger.info(f"最新模型: {latest_model_path}")
            self.logger.info("=" * 50)
            
            return str(final_model_path)
            
        except Exception as e:
            self.logger.error(f"保存模型失败: {str(e)}")
            return ""
    
    def _notify_progress(self, progress_data: Dict):
        """
        通知训练进度
        
        Args:
            progress_data: 进度数据字典
        """
        if self.progress_callback:
            try:
                self.progress_callback(progress_data)
            except Exception as e:
                self.logger.debug(f"进度回调执行失败: {str(e)}")
    
    def _notify_completion(self, success: bool, message: str):
        """
        通知训练完成
        
        Args:
            success: 是否成功
            message: 完成消息
        """
        if self.completion_callback:
            try:
                self.completion_callback(success, message)
            except Exception as e:
                self.logger.debug(f"完成回调执行失败: {str(e)}")
    
    @property
    def is_running(self) -> bool:
        """获取训练运行状态"""
        return self.is_training
    
    def validate_model(self, model_path: str) -> Dict:
        """
        验证模型性能
        
        Args:
            model_path: 模型文件路径
            
        Returns:
            Dict: 验证结果
        """
        try:
            if not Path(model_path).exists():
                return {'error': f'模型文件不存在: {model_path}'}
            
            model = YOLO(model_path)
            
            # 验证数据配置路径 - 优先使用主配置文件
            val_config = self.data_dir / "train_config.yaml"
            if not val_config.exists():
                val_config = self.data_dir / "train_simple.yaml"
            
            if not val_config.exists():
                return {'error': '验证数据配置文件不存在'}
            
            # 执行验证
            metrics = model.val(data=str(val_config), device=self.device)
            
            return {
                'map50': float(metrics.box.map50),
                'map50_95': float(metrics.box.map),
                'precision': float(metrics.box.mp),
                'recall': float(metrics.box.mr),
                'f1': float(metrics.box.f1)
            }
            
        except Exception as e:
            return {'error': f'模型验证失败: {str(e)}'}
    
    def get_available_models(self) -> List[str]:
        """
        获取可用的预训练模型列表
        
        Returns:
            List[str]: 模型名称列表
        """
        return [
            'yolo11n', 'yolo11s', 'yolo11m', 'yolo11l', 'yolo11x',
            'yolov8n', 'yolov8s', 'yolov8m', 'yolov8l', 'yolov8x'
        ]
    
    def get_trained_models(self) -> List[str]:
        """
        获取已训练的模型列表
        
        Returns:
            List[str]: 模型文件路径列表
        """
        trained_models = []
        
        # 查找runs目录中的模型文件
        if self.runs_dir.exists():
            for model_file in self.runs_dir.glob("fishing_model_*.pt"):
                trained_models.append(str(model_file))
        
        return sorted(trained_models, key=lambda x: Path(x).stat().st_mtime, reverse=True) 