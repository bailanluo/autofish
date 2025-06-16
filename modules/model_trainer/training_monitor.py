"""
训练监控界面 - 简化版
提供YOLO模型训练的基本监控功能
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import Dict, Optional
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from modules.logger import setup_logger, LogContext

# 导入核心组件
try:
    from .yolo_trainer import YOLOTrainer
    YOLO_TRAINER_AVAILABLE = True
except ImportError:
    YOLO_TRAINER_AVAILABLE = False

class TrainingMonitorApp:
    """训练监控主应用 - 简化版"""
    
    def __init__(self, config: Dict):
        """初始化训练监控应用"""
        self.config = config
        self.logger = setup_logger('TrainingMonitorApp')
        
        # 核心组件
        self.yolo_trainer = YOLOTrainer() if YOLO_TRAINER_AVAILABLE else None
        
        # 界面变量
        self.root = None
        self.training_active = False
        
        # 设置回调
        if self.yolo_trainer:
            self.yolo_trainer.set_progress_callback(self.on_training_progress)
            self.yolo_trainer.set_completion_callback(self.on_training_completion)
    
    def run(self):
        """启动训练监控应用"""
        with LogContext(self.logger, "启动训练监控应用"):
            self.create_main_window()
            self.root.mainloop()
    
    def create_main_window(self):
        """创建主窗口"""
        self.root = tk.Tk()
        self.root.title("🤖 YOLO模型训练监控 v2.3")
        self.root.geometry("800x600")
        
        # 创建界面
        self.create_widgets()
        
        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 配置框架
        config_frame = ttk.LabelFrame(main_frame, text="训练配置", padding="10")
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 模型选择
        ttk.Label(config_frame, text="模型类型:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.model_var = tk.StringVar(value="yolov8n")
        model_combo = ttk.Combobox(config_frame, textvariable=self.model_var)
        if self.yolo_trainer:
            model_combo['values'] = self.yolo_trainer.get_available_models()
        model_combo.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # 训练轮数
        ttk.Label(config_frame, text="训练轮数:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.epochs_var = tk.IntVar(value=100)
        ttk.Entry(config_frame, textvariable=self.epochs_var, width=10).grid(
            row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # 批次大小
        ttk.Label(config_frame, text="批次大小:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.batch_var = tk.IntVar(value=16)
        ttk.Entry(config_frame, textvariable=self.batch_var, width=10).grid(
            row=2, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # 学习率
        ttk.Label(config_frame, text="学习率:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.lr_var = tk.DoubleVar(value=0.01)
        ttk.Entry(config_frame, textvariable=self.lr_var, width=10).grid(
            row=3, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # 控制按钮
        button_frame = ttk.Frame(config_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(10, 0))
        
        self.start_btn = ttk.Button(button_frame, text="开始训练", command=self.start_training)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_btn = ttk.Button(button_frame, text="停止训练", 
                                  command=self.stop_training, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT)
        
        # 状态框架
        status_frame = ttk.LabelFrame(main_frame, text="训练状态", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        # 状态文本
        self.status_text = tk.Text(status_frame, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 进度条
        progress_frame = ttk.Frame(status_frame)
        progress_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(progress_frame, text="训练进度:").pack(anchor=tk.W)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=2)
    
    def start_training(self):
        """开始训练"""
        if not self.yolo_trainer:
            self.log_message("YOLO训练器不可用", "ERROR")
            return
            
        if self.training_active:
            self.log_message("训练已在进行中", "WARNING")
            return
        
        # 获取训练配置
        config = {
            'model_type': self.model_var.get(),
            'epochs': self.epochs_var.get(),
            'batch_size': self.batch_var.get(),
            'lr0': self.lr_var.get(),
            'imgsz': 640
        }
        
        self.log_message(f"开始训练 - 配置: {config}")
        
        # 更新UI状态
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.training_active = True
        
        # 启动训练
        if self.yolo_trainer.start_training(config):
            self.log_message("训练已启动")
        else:
            self.log_message("训练启动失败", "ERROR")
            self.stop_training()
    
    def stop_training(self):
        """停止训练"""
        if self.yolo_trainer:
            self.yolo_trainer.stop_training()
        
        self.training_active = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log_message("训练已停止")
    
    def on_training_progress(self, progress_data: Dict):
        """训练进度回调"""
        try:
            progress = progress_data.get('progress', 0)
            self.root.after(0, lambda: self.update_progress(progress_data))
        except Exception as e:
            self.logger.error(f"进度回调失败: {str(e)}")
    
    def on_training_completion(self, success: bool, message: str):
        """训练完成回调"""
        self.root.after(0, lambda: self.handle_completion(success, message))
    
    def update_progress(self, progress_data: Dict):
        """更新进度"""
        progress = progress_data.get('progress', 0)
        self.progress_var.set(progress)
        
        if 'epoch' in progress_data:
            epoch_info = f"轮次: {progress_data['epoch']}"
            if 'total_epochs' in progress_data:
                epoch_info += f"/{progress_data['total_epochs']}"
            self.log_message(epoch_info)
        
        if 'metrics' in progress_data:
            metrics = progress_data['metrics']
            if 'map50' in metrics:
                self.log_message(f"mAP50: {metrics['map50']:.3f}")
    
    def handle_completion(self, success: bool, message: str):
        """处理训练完成"""
        if success:
            self.log_message(f"✅ 训练完成: {message}")
        else:
            self.log_message(f"❌ 训练失败: {message}", "ERROR")
        
        self.stop_training()
    
    def log_message(self, message: str, level: str = "INFO"):
        """记录日志消息"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.status_text.insert(tk.END, formatted_message)
        self.status_text.see(tk.END)
    
    def on_closing(self):
        """关闭程序"""
        if self.training_active:
            if messagebox.askyesno("确认退出", "训练正在进行中，确定要退出吗？"):
                self.stop_training()
                self.root.destroy()
        else:
            self.root.destroy()

def main():
    """主函数"""
    try:
        config = {
            'data_dir': 'data',
            'model_dir': 'model', 
            'runs_dir': 'runs'
        }
        
        app = TrainingMonitorApp(config)
        app.run()
        
    except Exception as e:
        print(f"启动训练监控失败: {str(e)}")

if __name__ == "__main__":
    main() 