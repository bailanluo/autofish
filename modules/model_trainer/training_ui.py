"""
优化后的模型训练图形界面
去除冗余代码，使用配置管理器，提供专业的训练体验
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, font, filedialog
import threading
import queue
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from PIL import Image, ImageTk
import cv2

# 添加项目根目录到Python路径
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.append(str(ROOT_DIR))

from modules.logger import setup_logger, LogContext
from modules.model_trainer.config_manager import TrainingConfigManager

# 获取logger
logger = logging.getLogger(__name__)

class TrainingUI:
    """优化后的模型训练图形界面"""
    
    def __init__(self, root, pipeline):
        """
        初始化训练界面
        
        Args:
            root: Tkinter根窗口
            pipeline: 训练流程管理器实例
        """
        self.root = root
        self.pipeline = pipeline
        self.root.title("AutoFish 模型训练工具 v2.3")
        self.root.geometry("1200x800")
        
        # 初始化配置管理器
        self.config_manager = TrainingConfigManager()
        
        # 设置中文字体
        self.setup_chinese_font()
        
        # 初始化变量
        self.init_variables()
        
        # 创建界面
        self.create_widgets()
        
        # 启动进度监控
        self.monitor_training_progress()
        
    def setup_chinese_font(self):
        """设置中文字体"""
        try:
            chinese_fonts = ['Microsoft YaHei', 'SimHei', 'SimSun', 'KaiTi']
            self.chinese_font = None
            
            for font_name in chinese_fonts:
                try:
                    test_font = font.Font(family=font_name, size=10)
                    self.chinese_font = test_font
                    break
                except:
                    continue
                    
            if not self.chinese_font:
                self.chinese_font = font.Font(size=10)
                
        except Exception as e:
            logger.warning(f"设置中文字体失败: {str(e)}")
            self.chinese_font = None
    
    def init_variables(self):
        """初始化界面变量"""
        # 训练参数变量
        self.model_var = tk.StringVar(value="yolov8n")
        self.epochs_var = tk.StringVar(value="150")
        self.batch_var = tk.StringVar(value="16")
        self.lr_var = tk.StringVar(value="0.01")
        self.size_var = tk.StringVar(value="640")
        self.kfold_var = tk.StringVar(value="5")
        self.patience_var = tk.StringVar(value="50")  # 早停耐心值
        
        # 状态变量
        self.progress_var = tk.StringVar(value="等待开始训练...")
        self.status_var = tk.StringVar(value="就绪")
        
        # 验证界面变量
        self.validation_window = None
        self.confidence_var = tk.DoubleVar(value=0.5)
        self.current_image = None
        self.current_image_path = None
        
    def create_widgets(self):
        """创建主界面"""
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=2)
        self.root.rowconfigure(0, weight=1)
        
        # 左侧控制面板
        self.create_control_panel()
        
        # 右侧监控面板
        self.create_monitor_panel()
        
        # 底部状态栏
        self.create_status_bar()
        
        # 加载默认参数
        self.load_default_params()
        
    def create_control_panel(self):
        """创建左侧控制面板"""
        control_frame = ttk.LabelFrame(self.root, text="训练控制", padding="10")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # 数据管理部分
        self.create_data_section(control_frame)
        
        # 训练参数设置
        self.create_params_section(control_frame)
        
        # K折交叉验证设置
        self.create_kfold_section(control_frame)
        
        # 训练控制按钮
        self.create_control_buttons(control_frame)
        
    def create_data_section(self, parent):
        """创建数据管理部分"""
        data_frame = ttk.LabelFrame(parent, text="数据管理", padding="5")
        data_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(data_frame, text="扫描数据", command=self.scan_data).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(data_frame, text="检查依赖", command=self.check_dependencies).pack(side=tk.LEFT)
        
    def create_params_section(self, parent):
        """创建训练参数设置部分"""
        params_frame = ttk.LabelFrame(parent, text="训练参数", padding="5")
        params_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 模型选择
        ttk.Label(params_frame, text="模型类型:").grid(row=0, column=0, sticky=tk.W, pady=2)
        model_combo = ttk.Combobox(params_frame, textvariable=self.model_var, width=25)
        model_combo['values'] = self.config_manager.get_available_models()
        model_combo.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        model_combo.bind('<<ComboboxSelected>>', self.on_model_changed)
        
        # 模型帮助按钮
        ttk.Button(params_frame, text="?", width=3, command=self.show_model_help).grid(
            row=0, column=2, sticky=tk.W, padx=(5, 0), pady=2)
        
        # 训练轮数
        ttk.Label(params_frame, text="训练轮数:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(params_frame, textvariable=self.epochs_var, width=10).grid(
            row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # 批次大小
        ttk.Label(params_frame, text="批次大小:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Entry(params_frame, textvariable=self.batch_var, width=10).grid(
            row=2, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # 学习率
        ttk.Label(params_frame, text="学习率:").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Entry(params_frame, textvariable=self.lr_var, width=10).grid(
            row=3, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # 图片尺寸
        ttk.Label(params_frame, text="图片尺寸:").grid(row=4, column=0, sticky=tk.W, pady=2)
        size_combo = ttk.Combobox(params_frame, textvariable=self.size_var, width=10)
        size_combo['values'] = tuple(str(size) for size in self.config_manager.get_image_size_options())
        size_combo.grid(row=4, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # 图片尺寸帮助按钮
        ttk.Button(params_frame, text="?", width=3, command=self.show_image_size_help).grid(
            row=4, column=2, sticky=tk.W, padx=(5, 0), pady=2)
        
    def create_kfold_section(self, parent):
        """创建K折交叉验证设置部分"""
        kfold_frame = ttk.LabelFrame(parent, text="交叉验证", padding="5")
        kfold_frame.pack(fill=tk.X, pady=(0, 10))
        
        k_fold_config = self.config_manager.get_k_fold_config()
        
        ttk.Label(kfold_frame, text="K折数:").grid(row=0, column=0, sticky=tk.W, pady=2)
        kfold_combo = ttk.Combobox(kfold_frame, textvariable=self.kfold_var, width=10)
        kfold_combo['values'] = tuple(str(i) for i in range(
            k_fold_config['min_folds'], k_fold_config['max_folds'] + 1))
        kfold_combo.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # 早停配置
        ttk.Label(kfold_frame, text="早停耐心值:").grid(row=1, column=0, sticky=tk.W, pady=2)
        patience_entry = ttk.Entry(kfold_frame, textvariable=self.patience_var, width=10)
        patience_entry.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # 早停帮助按钮
        ttk.Button(kfold_frame, text="?", width=3, command=self.show_patience_help).grid(
            row=1, column=2, sticky=tk.W, padx=(5, 0), pady=2)
        
    def create_control_buttons(self, parent):
        """创建训练控制按钮"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.train_button = ttk.Button(button_frame, text="开始训练", command=self.start_training)
        self.train_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(button_frame, text="停止训练", 
                                     command=self.stop_training, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.validate_button = ttk.Button(button_frame, text="模型验证", 
                                         command=self.open_validation_window)
        self.validate_button.pack(side=tk.LEFT)
        
    def create_monitor_panel(self):
        """创建右侧监控面板"""
        monitor_frame = ttk.LabelFrame(self.root, text="训练监控", padding="10")
        monitor_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 进度显示
        progress_frame = ttk.LabelFrame(monitor_frame, text="训练进度", padding="5")
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(progress_frame, textvariable=self.progress_var).pack()
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        # 日志显示
        log_frame = ttk.LabelFrame(monitor_frame, text="训练日志", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建文本框和滚动条
        text_frame = ttk.Frame(log_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(text_frame, wrap=tk.WORD, font=self.chinese_font)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 清除日志按钮
        ttk.Button(log_frame, text="清除日志", command=self.clear_log).pack(pady=(5, 0))
        
    def create_status_bar(self):
        """创建底部状态栏"""
        status_frame = ttk.Frame(self.root)
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        ttk.Label(status_frame, text="状态:").pack(side=tk.LEFT)
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=(5, 0))
        
    def load_default_params(self):
        """加载默认参数"""
        try:
            # 获取当前选择的模型的默认参数
            current_model = self.model_var.get().split(' ')[0]
            default_params = self.config_manager.get_default_training_params(current_model)
            
            self.epochs_var.set(str(default_params['epochs']))
            self.batch_var.set(str(default_params['batch_size']))
            self.lr_var.set(str(default_params['learning_rate']))
            self.size_var.set(str(default_params['image_size']))
            
            # 设置K折默认值
            k_fold_config = self.config_manager.get_k_fold_config()
            self.kfold_var.set(str(k_fold_config['default_folds']))
            
            logger.info("默认参数加载完成")
            
        except Exception as e:
            logger.error(f"加载默认参数失败: {str(e)}")
    
    def on_model_changed(self, event=None):
        """模型选择改变时的回调"""
        self.load_default_params()
        
    def validate_params(self) -> bool:
        """验证训练参数"""
        try:
            params = {
                'epochs': int(self.epochs_var.get()),
                'batch_size': int(self.batch_var.get()),
                'learning_rate': float(self.lr_var.get()),
                'image_size': int(self.size_var.get()),
                'patience': int(self.patience_var.get())
            }
            
            # 验证早停参数
            if params['patience'] < 1:
                messagebox.showerror("参数错误", "早停耐心值必须大于0")
                return False
            if params['patience'] > params['epochs']:
                messagebox.showerror("参数错误", "早停耐心值不应大于训练轮数")
                return False
            
            errors = self.config_manager.validate_training_params(params)
            
            if errors:
                error_msg = "参数验证失败:\n" + "\n".join(f"• {field}: {msg}" for field, msg in errors.items())
                messagebox.showerror("参数错误", error_msg)
                return False
                
            return True
            
        except ValueError as e:
            messagebox.showerror("参数错误", f"参数格式错误: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"参数验证异常: {str(e)}")
            messagebox.showerror("验证错误", f"参数验证时发生错误: {str(e)}")
            return False
    
    def show_model_help(self):
        """显示模型帮助信息"""
        self.show_help_window("模型类型详细说明", self.config_manager.get_help_text("model_help"))
        
    def show_image_size_help(self):
        """显示图片尺寸帮助信息"""
        self.show_help_window("图片尺寸参数详细说明", self.config_manager.get_help_text("image_size_help"))
    
    def show_patience_help(self):
        """显示早停耐心值帮助"""
        help_text = """早停耐心值 (Patience) 说明：

🎯 **作用**：防止过拟合，提高训练效率
- 当验证指标连续N轮没有改善时，自动停止训练
- 避免无效的长时间训练，节省时间和资源

📊 **监控指标**：
- 检测模型：mAP50 (平均精度)
- 分类模型：准确率 (Accuracy)

⚙️ **推荐设置**：
- 小数据集：20-30 (快速收敛)
- 中等数据集：30-50 (平衡效果)
- 大数据集：50-100 (充分训练)

💡 **工作原理**：
1. 每轮训练后检查验证指标
2. 如果指标改善，重置计数器
3. 如果连续N轮无改善，触发早停
4. 自动保存最佳模型权重

✅ **优势**：
- 防止过拟合
- 节省训练时间
- 自动找到最佳停止点
- 保证模型泛化能力"""
        self.show_help_window("早停机制说明", help_text)
        
    def show_help_window(self, title: str, content: str):
        """显示帮助窗口"""
        help_window = tk.Toplevel(self.root)
        help_window.title(title)
        help_window.geometry("700x800")
        help_window.resizable(True, True)
        
        # 创建滚动文本框
        text_frame = ttk.Frame(help_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=self.chinese_font)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 插入帮助文本
        text_widget.insert(tk.END, content)
        text_widget.config(state=tk.DISABLED)
        
        # 关闭按钮
        button_frame = ttk.Frame(help_window)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        ttk.Button(button_frame, text="关闭", command=help_window.destroy).pack(side=tk.RIGHT)
        
        # 居中显示
        help_window.transient(self.root)
        help_window.grab_set()
        self.center_window(help_window, 700, 800)
    
    def center_window(self, window, width, height):
        """居中显示窗口"""
        window.update_idletasks()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")
    
    def check_dependencies(self):
        """检查依赖"""
        self.log_message("正在检查依赖...")
        # 这里可以添加具体的依赖检查逻辑
        self.log_message("依赖检查完成")
        
    def scan_data(self):
        """扫描数据"""
        self.log_message("正在扫描训练数据...")
        try:
            # 使用训练流程的数据处理器扫描数据
            class_counts = self.pipeline.data_processor.scan_data()
            if class_counts:
                total_images = sum(class_counts.values())
                self.log_message(f"发现 {len(class_counts)} 个类别，共 {total_images} 张图片")
                for class_name, count in class_counts.items():
                    if count > 0:
                        self.log_message(f"  - {class_name}: {count} 张")
                self.log_message("数据扫描完成")
            else:
                self.log_message("未找到训练数据，请检查 data/raw/images/ 目录")
        except Exception as e:
            self.log_message(f"数据扫描失败: {str(e)}")
        
    def start_training(self):
        """开始训练"""
        if not self.validate_params():
            return
            
        self.train_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_var.set("训练中...")
        
        # 获取训练参数，适配新的TrainingPipeline接口
        config = {
            'model_type': self.model_var.get().split(' ')[0],
            'epochs': int(self.epochs_var.get()),
            'batch_size': int(self.batch_var.get()),
            'lr0': float(self.lr_var.get()),
            'imgsz': int(self.size_var.get()),
            'patience': int(self.patience_var.get()),
            'train_ratio': 0.8,
            'val_ratio': 0.2,
            'force_recreate_data': False
        }
        
        self.log_message(f"开始完整训练流程 - 配置: {config}")
        
        # 设置训练流程回调
        self.pipeline.set_progress_callback(self._on_training_progress)
        self.pipeline.set_completion_callback(self._on_training_completion)
        
        # 启动训练线程
        training_thread = threading.Thread(target=self._run_training, args=(config,))
        training_thread.daemon = True
        training_thread.start()
    
    def _run_training(self, config):
        """运行训练流程"""
        try:
            success = self.pipeline.run_complete_training(config)
            if not success:
                self.log_message("训练启动失败")
                self._reset_ui_state()
        except Exception as e:
            self.log_message(f"训练异常: {str(e)}")
            self._reset_ui_state()
    
    def _on_training_progress(self, stage: str, data: dict):
        """训练进度回调"""
        try:
            progress = data.get('progress', 0)
            self.root.after(0, lambda: self._update_progress_ui(stage, progress, data))
        except Exception as e:
            logger.error(f"进度回调失败: {str(e)}")
    
    def _on_training_completion(self, success: bool, message: str, data: dict):
        """训练完成回调"""
        try:
            self.root.after(0, lambda: self._handle_training_completion(success, message, data))
        except Exception as e:
            logger.error(f"完成回调失败: {str(e)}")
    
    def _update_progress_ui(self, stage: str, progress: float, data: dict):
        """更新进度界面"""
        self.progress_bar['value'] = progress
        self.progress_var.set(f"{stage}: {progress:.1f}%")
        self.status_var.set(stage)
        
        # 显示详细信息
        if 'epoch' in data and 'total_epochs' in data:
            epoch = data['epoch']
            total_epochs = data['total_epochs']
            epoch_info = f"轮次: {epoch}/{total_epochs}"
            
            # 检查是否有指标信息
            if 'metrics' in data and data['metrics']:
                metrics = data['metrics']
                map50 = metrics.get('map50', 0.0)
                
                # 只有当map50不为0时才显示（避免显示错误的0值）
                if map50 > 0:
                    self.log_message(f"模型训练 - {epoch_info}")
                    self.log_message(f"mAP50: {map50:.3f}")
                    
                    # 显示其他指标（如果有的话）
                    if 'precision' in metrics and metrics['precision'] > 0:
                        self.log_message(f"精确度: {metrics['precision']:.3f}")
                    if 'recall' in metrics and metrics['recall'] > 0:
                        self.log_message(f"召回率: {metrics['recall']:.3f}")
                else:
                    # 如果没有有效指标，只显示轮次信息
                    self.log_message(f"模型训练 - {epoch_info}")
            else:
                # 没有指标信息时，只显示轮次
                self.log_message(f"模型训练 - {epoch_info}")
        else:
            # 没有轮次信息时，显示阶段信息
            self.log_message(f"{stage} - 进度: {progress:.1f}%")
    
    def _handle_training_completion(self, success: bool, message: str, data: dict):
        """处理训练完成"""
        if success:
            self.log_message(f"✅ 训练完成: {message}")
            if 'latest_training_dir' in data:
                self.log_message(f"训练结果: {data['latest_training_dir']}")
            if 'trained_models' in data:
                self.log_message(f"训练模型: {len(data['trained_models'])} 个")
        else:
            self.log_message(f"❌ 训练失败: {message}")
        
        self._reset_ui_state()
    
    def _reset_ui_state(self):
        """重置UI状态"""
        self.train_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("就绪")
        self.progress_bar['value'] = 0
        self.progress_var.set("等待开始训练...")
        
    def stop_training(self):
        """停止训练"""
        self.pipeline.stop_training()
        self._reset_ui_state()
        self.status_var.set("已停止")
        self.log_message("训练已停止")
        
    def clear_log(self):
        """清除日志"""
        self.log_text.delete(1.0, tk.END)
        
    def log_message(self, message):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, formatted_message)
        self.log_text.see(tk.END)
        
    def monitor_training_progress(self):
        """监控训练进度（简化版，主要通过回调处理）"""
        try:
            # 检查训练状态
            if hasattr(self.pipeline, 'is_running') and self.pipeline.is_running:
                if self.status_var.get() == "就绪":
                    self.status_var.set("训练中...")
            
        except Exception as e:
            logger.error(f"监控进度失败: {str(e)}")
        
        # 继续监控
        self.root.after(1000, self.monitor_training_progress)
    
    def open_validation_window(self):
        """打开模型验证窗口 - 启动桌面测试工具"""
        try:
            import subprocess
            import sys
            
            # 获取桌面测试工具的路径
            desktop_tester_path = os.path.join(
                os.path.dirname(__file__), 
                "desktop_tester.py"
            )
            
            # 检查文件是否存在
            if not os.path.exists(desktop_tester_path):
                messagebox.showerror("错误", f"桌面测试工具未找到: {desktop_tester_path}")
                return
            
            # 启动桌面测试工具
            self.log_message("正在启动桌面测试工具...")
            
            # 使用subprocess启动独立进程
            subprocess.Popen([
                sys.executable, 
                desktop_tester_path
            ], cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            
            self.log_message("✅ 桌面测试工具已启动")
            
        except Exception as e:
            error_msg = f"启动桌面测试工具失败: {str(e)}"
            self.log_message(f"❌ {error_msg}")
            messagebox.showerror("启动失败", error_msg)
    
    def run(self):
        """运行界面"""
        self.root.mainloop() 