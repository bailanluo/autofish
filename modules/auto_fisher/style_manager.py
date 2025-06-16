#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
样式管理器模块

该模块提供统一的UI样式管理功能，包括主题、颜色、字体等。
"""

import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, Any, Optional

# 导入配置管理器
from modules.auto_fisher.config_manager import get_instance as get_config_manager


class StyleManager:
    """
    样式管理器类
    
    提供统一的UI样式管理功能，包括主题、颜色、字体等。
    """
    
    def __init__(self):
        """
        初始化样式管理器
        """
        # 获取配置管理器
        self.config_manager = get_config_manager()
        
        # 获取UI配置
        self.ui_config = self.config_manager.get_ui_config()
        
        # 获取主题配置
        self.theme = self.ui_config['theme']
        
        # 默认字体
        self.default_font = ("Arial", 10)
        
        # 创建样式
        self.style = ttk.Style()
        
        # 应用样式
        self._apply_style()
        
        logging.info("样式管理器初始化完成")
    
    def _apply_style(self):
        """
        应用样式到ttk组件
        """
        try:
            # 尝试设置主题
            available_themes = self.style.theme_names()
            if 'clam' in available_themes:
                self.style.theme_use('clam')
            
            # 配置颜色
            bg_color = self.theme['background_color']
            button_color = self.theme['button_color']
            text_color = self.theme['text_color']
            accent_color = self.theme['accent_color']
            
            # 配置ttk组件样式
            self.style.configure('TFrame', background=bg_color)
            self.style.configure('TLabel', background=bg_color, foreground=text_color)
            self.style.configure('TButton', background=button_color, foreground=text_color)
            self.style.configure('TCheckbutton', background=bg_color, foreground=text_color)
            self.style.configure('TRadiobutton', background=bg_color, foreground=text_color)
            self.style.configure('TEntry', background=bg_color, foreground=text_color)
            self.style.configure('TLabelframe', background=bg_color, foreground=text_color)
            self.style.configure('TLabelframe.Label', background=bg_color, foreground=text_color)
            self.style.configure('TNotebook', background=bg_color)
            self.style.configure('TNotebook.Tab', background=bg_color, foreground=text_color)
            
            # 配置按钮鼠标悬停效果
            self.style.map('TButton',
                background=[('active', accent_color)],
                foreground=[('active', 'white')])
            
            # 配置选中效果
            self.style.map('TCheckbutton',
                background=[('active', bg_color)],
                foreground=[('active', accent_color)])
            
            self.style.map('TRadiobutton',
                background=[('active', bg_color)],
                foreground=[('active', accent_color)])
            
            # 配置选项卡效果
            self.style.map('TNotebook.Tab',
                background=[('selected', accent_color)],
                foreground=[('selected', 'white')])
            
            logging.info("样式已应用")
            
        except Exception as e:
            logging.error(f"应用样式时出错: {str(e)}")
    
    def configure_widget(self, widget: tk.Widget):
        """
        配置单个小部件的样式
        
        Args:
            widget: 要配置样式的小部件
        """
        try:
            bg_color = self.theme['background_color']
            text_color = self.theme['text_color']
            
            # 根据小部件类型应用不同的样式
            widget_type = widget.winfo_class()
            
            if widget_type in ('Toplevel', 'Tk', 'Frame'):
                widget.configure(background=bg_color)
            
            elif widget_type in ('Label', 'Message'):
                widget.configure(background=bg_color, foreground=text_color)
            
            elif widget_type in ('Button'):
                widget.configure(
                    background=self.theme['button_color'],
                    foreground=text_color,
                    activebackground=self.theme['accent_color'],
                    activeforeground='white'
                )
            
            # 递归配置子小部件
            for child in widget.winfo_children():
                self.configure_widget(child)
                
        except Exception as e:
            logging.error(f"配置小部件样式时出错: {str(e)}")
    
    def get_main_window_style(self) -> Dict[str, Any]:
        """
        获取主窗口样式
        
        Returns:
            包含主窗口样式的字典
        """
        # 增大窗口默认尺寸，确保所有组件显示完整
        return {
            'title': self.ui_config['title'],
            'size': (700, 600),  # 修改为更大的尺寸
            'position': (self.ui_config['position']['x'], self.ui_config['position']['y']),
            'background': self.theme['background_color']
        }
    
    def get_button_style(self) -> Dict[str, Any]:
        """
        获取按钮样式
        
        Returns:
            包含按钮样式的字典
        """
        return {
            'background': self.theme['button_color'],
            'foreground': self.theme['text_color'],
            'activebackground': self.theme['accent_color'],
            'activeforeground': 'white',
            'font': self.default_font,
            'borderwidth': 1,
            'relief': tk.RAISED,
            'padx': 10,
            'pady': 5
        }
    
    def get_label_style(self) -> Dict[str, Any]:
        """
        获取标签样式
        
        Returns:
            包含标签样式的字典
        """
        return {
            'background': self.theme['background_color'],
            'foreground': self.theme['text_color'],
            'font': self.default_font,
            'padx': 5,
            'pady': 5
        }
    
    def get_frame_style(self) -> Dict[str, Any]:
        """
        获取框架样式
        
        Returns:
            包含框架样式的字典
        """
        return {
            'background': self.theme['background_color'],
            'padx': 10,
            'pady': 10,
            'borderwidth': 0
        }
    
    def get_statusbar_style(self) -> Dict[str, Any]:
        """
        获取状态栏样式
        
        Returns:
            包含状态栏样式的字典
        """
        return {
            'background': self.theme['background_color'],
            'foreground': self.theme['accent_color'],
            'font': ("Arial", 9),
            'relief': tk.SUNKEN,
            'anchor': tk.W,
            'padx': 5,
            'pady': 2
        }


# 单例模式
_instance = None

def get_instance():
    """
    获取样式管理器单例
    
    Returns:
        StyleManager实例
    """
    global _instance
    if _instance is None:
        _instance = StyleManager()
    return _instance 