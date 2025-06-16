#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
钓鱼状态显示窗口模块

该模块实现一个简单的状态显示窗口，用于实时显示钓鱼状态。
"""

import tkinter as tk
import threading
import logging
import time
from typing import Optional, Dict, List, Callable

# 导入相关模块
from modules.auto_fisher.fishing_state_machine import FishingState


class StatusDisplay:
    """
    钓鱼状态显示窗口类
    
    实现一个简单的状态显示窗口，用于实时显示钓鱼状态。
    """
    
    def __init__(self):
        """
        初始化状态显示窗口
        """
        self.root = None
        self.state_label = None
        self.time_label = None
        self.click_label = None
        self.direction_label = None
        
        # 当前状态
        self.current_state = "初始化中..."
        
        # 开始时间
        self.start_time = time.time()
        
        # 点击计数
        self.click_count = 0
        
        # 方向状态
        self.direction = "无"
        
        # 运行标志
        self.is_running = False
        
        # 窗口线程
        self.thread = None
        
        # 更新锁
        self.update_lock = threading.Lock()
        
        logging.info("状态显示窗口初始化完成")
    
    def start(self):
        """
        启动状态显示窗口
        """
        if self.is_running:
            logging.warning("状态显示窗口已在运行中")
            return
        
        # 如果已有窗口，先销毁
        if self.root:
            try:
                self.root.destroy()
            except Exception as e:
                logging.error(f"销毁旧窗口时出错: {str(e)}")
        
        # 设置运行标志
        self.is_running = True
        
        # 重置开始时间
        self.start_time = time.time()
        
        # 重置点击计数
        self.click_count = 0
        
        # 重置方向状态
        self.direction = "无"
        
        # 启动窗口线程
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        
        logging.info("状态显示窗口已启动")
    
    def stop(self):
        """
        停止状态显示窗口
        """
        if not self.is_running:
            return
        
        # 设置运行标志
        self.is_running = False
        
        # 等待线程结束
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        
        # 销毁窗口
        if self.root:
            try:
                self.root.destroy()
            except Exception as e:
                logging.error(f"销毁窗口时出错: {str(e)}")
        
        # 重置窗口引用
        self.root = None
        self.state_label = None
        self.time_label = None
        self.click_label = None
        self.direction_label = None
        
        logging.info("状态显示窗口已停止")
    
    def update_state(self, state: str):
        """
        更新状态
        
        Args:
            state: 状态名称
        """
        with self.update_lock:
            self.current_state = state
    
    def update_click_count(self, count: int):
        """
        更新点击计数
        
        Args:
            count: 点击计数
        """
        with self.update_lock:
            self.click_count = count
    
    def update_direction(self, direction: str):
        """
        更新方向状态
        
        Args:
            direction: 方向状态
        """
        with self.update_lock:
            self.direction = direction
    
    def _run(self):
        """
        运行状态显示窗口
        """
        try:
            # 创建主窗口
            self.root = tk.Tk()
            self.root.title("")  # 无标题
            self.root.geometry("300x50+10+10")  # 大小和位置（左上角）
            self.root.attributes("-topmost", True)  # 窗口置顶
            self.root.attributes("-alpha", 1.0)  # 窗口完全不透明
            self.root.overrideredirect(True)  # 无边框
            self.root.configure(bg="black")  # 黑色背景
            self.root.attributes("-transparentcolor", "black")  # 将黑色设为透明色
            self.root.protocol("WM_DELETE_WINDOW", self._on_close)  # 处理关闭事件
            
            # 创建状态标签
            self.state_label = tk.Label(self.root, text="状态: 初始化中...", font=("Arial", 14, "bold"), 
                                        fg="yellow", bg="black")
            self.state_label.pack(pady=10)
            
            # 不再创建其他标签
            self.time_label = None
            self.click_label = None
            self.direction_label = None
            
            # 启动更新定时器
            self._update_labels()
            
            # 运行主循环
            self.root.mainloop()
            
        except Exception as e:
            logging.error(f"创建状态显示窗口时出错: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            self.is_running = False
    
    def _update_labels(self):
        """
        更新标签
        """
        if not self.is_running or not self.root:
            return
        
        try:
            # 获取当前状态
            with self.update_lock:
                current_state = self.current_state
            
            # 更新状态标签
            if self.state_label:
                self.state_label.config(text=f"状态: {current_state}")
            
            # 定时更新
            if self.root:
                self.root.after(100, self._update_labels)
                
        except Exception as e:
            logging.error(f"更新标签时出错: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
    
    def _on_close(self):
        """
        处理关闭事件
        """
        logging.info("用户关闭状态显示窗口")
        self.stop()


# 单例模式
_instance = None
_instance_lock = threading.Lock()

def get_instance():
    """
    获取状态显示窗口单例
    
    Returns:
        StatusDisplay实例
    """
    global _instance
    with _instance_lock:
        if _instance is None:
            _instance = StatusDisplay()
        return _instance 