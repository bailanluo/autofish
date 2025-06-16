#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AutoFish v2.3主程序入口

该模块是AutoFish v2.3的主入口，用于选择和启动各个功能模块。
"""

import os
import sys
import logging
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
from pathlib import Path

# 设置项目根目录
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 导入日志模块
from modules.logger import setup_logger


class MainApp:
    """
    AutoFish v2.3主程序
    
    用于选择和启动各个功能模块。
    """
    
    def __init__(self, root):
        """
        初始化主程序
        
        Args:
            root: 根窗口
        """
        # 根窗口
        self.root = root
        
        # 设置窗口标题
        root.title("AutoFish v2.3")
        
        # 设置窗口大小和位置
        root.geometry("500x400+300+200")
        root.resizable(False, False)
        
        # 设置窗口图标
        try:
            icon_path = os.path.join("assets", "icons", "fishing.ico")
            if os.path.exists(icon_path):
                root.iconbitmap(icon_path)
        except Exception as e:
            logging.warning(f"设置窗口图标失败: {str(e)}")
        
        # 创建界面
        self.create_widgets()
        
        # 设置窗口关闭事件
        root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def create_widgets(self):
        """
        创建界面控件
        """
        # 主框架
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # 标题标签
        title_label = tk.Label(
            main_frame, 
            text="AutoFish v2.3",
            font=("Arial", 24, "bold"),
        )
        title_label.pack(pady=(0, 20))
        
        # 副标题
        subtitle_label = tk.Label(
            main_frame,
            text="基于YOLO深度学习的智能钓鱼辅助工具",
            font=("Arial", 12)
        )
        subtitle_label.pack(pady=(0, 30))
        
        # 模块选择标签
        module_label = tk.Label(
            main_frame,
            text="请选择要启动的功能模块:",
            font=("Arial", 10, "bold"),
            anchor="w"
        )
        module_label.pack(fill="x", pady=(0, 10))
        
        # 按钮样式
        button_style = {
            "font": ("Arial", 12),
            "width": 20,
            "height": 2,
            "relief": tk.RAISED,
            "borderwidth": 2
        }
        
        # 模块按钮框架
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        # 数据采集按钮
        data_collector_button = tk.Button(
            button_frame,
            text="数据采集模块",
            command=self.launch_data_collector,
            **button_style,
            bg="#3498db",
            fg="white"
        )
        data_collector_button.pack(pady=10)
        
        # 模型训练按钮
        model_trainer_button = tk.Button(
            button_frame,
            text="模型训练模块",
            command=self.launch_model_trainer,
            **button_style,
            bg="#2ecc71",
            fg="white"
        )
        model_trainer_button.pack(pady=10)
        
        # 自动钓鱼按钮
        auto_fisher_button = tk.Button(
            button_frame,
            text="自动钓鱼模块",
            command=self.launch_auto_fisher,
            **button_style,
            bg="#e74c3c",
            fg="white"
        )
        auto_fisher_button.pack(pady=10)
        
        # 底部状态栏
        status_frame = tk.Frame(main_frame)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))
        
        version_label = tk.Label(status_frame, text="版本: v2.3", anchor="e")
        version_label.pack(side=tk.RIGHT)
        
        status_label = tk.Label(status_frame, text="就绪", anchor="w")
        status_label.pack(side=tk.LEFT)
        
        self.status_label = status_label
    
    def launch_data_collector(self):
        """
        启动数据采集模块
        """
        self.status_label.config(text="正在启动数据采集模块...")
        self.root.update()
        
        try:
            # 构建模块路径
            module_path = os.path.join(project_root, "modules", "data_collector", "main.py")
            
            # 启动子进程
            subprocess.Popen([sys.executable, module_path])
            
            self.status_label.config(text="数据采集模块已启动")
            
        except Exception as e:
            logging.error(f"启动数据采集模块失败: {str(e)}")
            messagebox.showerror("错误", f"启动数据采集模块失败: {str(e)}")
            self.status_label.config(text="启动失败")
    
    def launch_model_trainer(self):
        """
        启动模型训练模块
        """
        self.status_label.config(text="正在启动模型训练模块...")
        self.root.update()
        
        try:
            # 构建模块路径
            module_path = os.path.join(project_root, "modules", "model_trainer", "main.py")
            
            # 启动子进程
            subprocess.Popen([sys.executable, module_path])
            
            self.status_label.config(text="模型训练模块已启动")
            
        except Exception as e:
            logging.error(f"启动模型训练模块失败: {str(e)}")
            messagebox.showerror("错误", f"启动模型训练模块失败: {str(e)}")
            self.status_label.config(text="启动失败")
    
    def launch_auto_fisher(self):
        """
        启动自动钓鱼模块
        """
        self.status_label.config(text="正在启动自动钓鱼模块...")
        self.root.update()
        
        try:
            # 构建模块路径
            module_path = os.path.join(project_root, "modules", "auto_fisher", "main.py")
            
            # 启动子进程
            subprocess.Popen([sys.executable, module_path])
            
            self.status_label.config(text="自动钓鱼模块已启动")
            
        except Exception as e:
            logging.error(f"启动自动钓鱼模块失败: {str(e)}")
            messagebox.showerror("错误", f"启动自动钓鱼模块失败: {str(e)}")
            self.status_label.config(text="启动失败")
    
    def on_close(self):
        """
        窗口关闭事件处理
        """
        # 确认退出
        if messagebox.askokcancel("退出", "确定要退出AutoFish吗？"):
            self.root.destroy()


def main():
    """
    主函数
    """
    # 创建日志目录
    log_dir = os.path.join(project_root, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # 设置日志
    setup_logger('autofish_main', log_dir)
    
    # 记录启动日志
    logging.info("AutoFish v2.3主程序启动")
    
    # 创建主窗口
    root = tk.Tk()
    app = MainApp(root)
    
    try:
        # 运行主循环
        root.mainloop()
    except Exception as e:
        logging.error(f"运行主程序出错: {str(e)}")
        raise
    finally:
        logging.info("AutoFish v2.3主程序结束")


if __name__ == "__main__":
    main() 