#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
UI管理器模块

该模块负责钓鱼脚本的图形用户界面，包括主窗口和相关控件。
"""

import os
import sys
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any

# 导入相关模块
from modules.auto_fisher.config_manager import get_instance as get_config_manager
from modules.auto_fisher.business_logic import get_instance as get_business_logic
from modules.auto_fisher.style_manager import get_instance as get_style_manager
from modules.auto_fisher.settings_dialog import SettingsDialog


class UIManager:
    """
    UI管理器类
    
    负责钓鱼脚本的图形用户界面，包括主窗口和相关控件。
    """
    
    def __init__(self):
        """
        初始化UI管理器
        """
        # 获取相关模块实例
        self.config_manager = get_config_manager()
        self.business_logic = get_business_logic()
        self.style_manager = get_style_manager()
        
        # 获取UI配置
        self.ui_config = self.config_manager.get_ui_config()
        
        # 主窗口
        self.root: Optional[tk.Tk] = None
        
        # 设置对话框
        self.settings_dialog: Optional[SettingsDialog] = None
        
        # 控件
        self.status_label: Optional[tk.Label] = None
        self.start_button: Optional[tk.Button] = None
        self.stop_button: Optional[tk.Button] = None
        
        # 初始化UI
        self._init_ui()
        
        logging.info("UI管理器初始化完成")
    
    def _init_ui(self):
        """
        初始化UI界面
        """
        # 创建主窗口
        self.root = tk.Tk()
        
        # 获取主窗口样式
        main_style = self.style_manager.get_main_window_style()
        
        # 设置窗口标题
        self.root.title(main_style['title'])
        
        # 设置窗口大小
        width, height = main_style['size']
        self.root.geometry(f"{width}x{height}")
        
        # 设置窗口位置
        x, y = main_style['position']
        self.root.geometry(f"+{x}+{y}")
        
        # 设置窗口样式
        self.root.configure(background=main_style['background'])
        
        # 设置窗口图标
        try:
            icon_path = os.path.join("assets", "icons", "fishing.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            logging.warning(f"设置窗口图标失败: {str(e)}")
        
        # 创建界面控件
        self._create_widgets()
        
        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # 设置业务逻辑的状态回调
        self.business_logic.set_status_callback(self._update_status)
    
    def _create_widgets(self):
        """
        创建界面控件
        """
        # 获取样式
        button_style = self.style_manager.get_button_style()
        label_style = self.style_manager.get_label_style()
        frame_style = self.style_manager.get_frame_style()
        
        # 创建主框架
        main_frame = tk.Frame(self.root, **frame_style)
        main_frame.pack(fill="both", expand=True)
        
        # 标题标签
        title_label = tk.Label(
            main_frame, 
            text="AutoFish - 自动钓鱼",
            **{**label_style, "font": ("Arial", 18, "bold")}
        )
        title_label.pack(pady=15)
        
        # 按钮框架
        button_frame = tk.Frame(main_frame, **frame_style)
        button_frame.pack(pady=10)
        
        # 开始按钮
        self.start_button = tk.Button(
            button_frame,
            text="开始钓鱼",
            command=self._on_start_click,
            width=15,
            height=2,
            **button_style
        )
        self.start_button.pack(side="left", padx=10)
        
        # 停止按钮
        self.stop_button = tk.Button(
            button_frame,
            text="停止钓鱼",
            command=self._on_stop_click,
            width=15,
            height=2,
            state=tk.DISABLED,
            **button_style
        )
        self.stop_button.pack(side="left", padx=10)
        
        # 设置按钮
        settings_button = tk.Button(
            button_frame,
            text="设置",
            command=self._on_settings_click,
            width=10,
            height=2,
            **button_style
        )
        settings_button.pack(side="left", padx=10)
        
        # 热键提示框架
        hotkey_frame = tk.Frame(main_frame, **frame_style)
        hotkey_frame.pack(pady=15)
        
        # 获取热键配置
        hotkeys = self.config_manager.get_hotkeys()
        
        # 热键提示标签
        hotkey_label = tk.Label(
            hotkey_frame,
            text=f"快捷键: 开始/停止 - {hotkeys['start']}    |    紧急停止 - {hotkeys['stop']}",
            **label_style
        )
        hotkey_label.pack()
        
        # 状态框架
        status_frame = tk.Frame(main_frame, **frame_style)
        status_frame.pack(fill="x", side="bottom", pady=10)
        
        # 状态标签
        self.status_label = tk.Label(
            status_frame,
            text="就绪",
            anchor="w",
            **label_style
        )
        self.status_label.pack(fill="x")
        
        # 版本标签
        version_label = tk.Label(
            status_frame,
            text="AutoFish v2.3",
            anchor="e",
            **label_style
        )
        version_label.pack(fill="x")
    
    def run(self):
        """
        运行UI主循环
        """
        if not self.root:
            logging.error("UI未初始化")
            return
        
        try:
            # 启动热键监听
            self.business_logic.start_hotkey_listener()
            
            # 启动主循环
            self.root.mainloop()
            
        except Exception as e:
            logging.error(f"运行UI主循环出错: {str(e)}")
    
    def _on_close(self):
        """
        窗口关闭事件处理
        """
        try:
            # 确认是否退出
            if messagebox.askokcancel("退出", "确定要退出自动钓鱼吗？"):
                # 停止钓鱼
                if self.business_logic.is_fishing_active():
                    self.business_logic.stop_fishing()
                
                # 停止热键监听
                self.business_logic.stop_hotkey_listener()
                
                # 退出程序
                self.root.destroy()
                
                # 强制终止程序
                import sys
                sys.exit(0)
                
        except Exception as e:
            logging.error(f"处理窗口关闭事件出错: {str(e)}")
            self.root.destroy()
            
            # 强制终止程序
            import sys
            sys.exit(1)
    
    def _on_start_click(self):
        """
        开始按钮点击事件处理
        """
        try:
            # 禁用开始按钮
            self.start_button.config(state=tk.DISABLED)
            
            # 启用停止按钮
            self.stop_button.config(state=tk.NORMAL)
            
            # 启动钓鱼
            self.business_logic.start_fishing()
            
        except Exception as e:
            logging.error(f"处理开始按钮点击事件出错: {str(e)}")
            messagebox.showerror("错误", f"启动钓鱼失败: {str(e)}")
            
            # 恢复按钮状态
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
    
    def _on_stop_click(self):
        """
        停止按钮点击事件处理
        """
        try:
            # 禁用停止按钮
            self.stop_button.config(state=tk.DISABLED)
            
            # 启用开始按钮
            self.start_button.config(state=tk.NORMAL)
            
            # 停止钓鱼
            self.business_logic.stop_fishing()
            
        except Exception as e:
            logging.error(f"处理停止按钮点击事件出错: {str(e)}")
            messagebox.showerror("错误", f"停止钓鱼失败: {str(e)}")
            
            # 恢复按钮状态
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
    
    def _on_settings_click(self):
        """
        设置按钮点击事件处理
        """
        try:
            # 创建设置对话框
            if not self.settings_dialog:
                self.settings_dialog = SettingsDialog(self.root)
            
            # 设置热键回调
            self.settings_dialog.set_hotkey_callback(self.business_logic.update_hotkey)
            
            # 显示设置对话框
            self.settings_dialog.show()
            
        except Exception as e:
            logging.error(f"处理设置按钮点击事件出错: {str(e)}")
            messagebox.showerror("错误", f"打开设置对话框失败: {str(e)}")
    
    def _update_status(self, status: str):
        """
        更新状态标签
        
        Args:
            status: 状态信息
        """
        if not self.status_label:
            return
        
        try:
            self.status_label.config(text=status)
            
            # 如果钓鱼已停止，恢复按钮状态
            if status.startswith("钓鱼已停止"):
                self.start_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.DISABLED)
                
        except Exception as e:
            logging.error(f"更新状态标签出错: {str(e)}")


# 单例模式
_instance = None

def get_instance():
    """
    获取UI管理器单例
    
    Returns:
        UIManager实例
    """
    global _instance
    if _instance is None:
        _instance = UIManager()
    return _instance 