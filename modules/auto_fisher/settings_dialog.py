#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
设置对话框模块

该模块提供一个设置对话框，用于配置钓鱼脚本的热键和状态显示设置。
"""

import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Dict, Any, Optional

# 导入相关模块
from modules.auto_fisher.config_manager import get_instance as get_config_manager
from modules.auto_fisher.status_display import get_instance as get_status_display


class SettingsDialog:
    """
    设置对话框类
    
    提供一个对话框，用于配置钓鱼脚本的各种设置。
    """
    
    def __init__(self, parent):
        """
        初始化设置对话框
        
        Args:
            parent: 父窗口
        """
        # 父窗口
        self.parent = parent
        
        # 获取配置管理器
        self.config_manager = get_config_manager()
        
        # 获取状态显示组件
        self.status_display = get_status_display()
        
        # 对话框窗口
        self.dialog: Optional[tk.Toplevel] = None
        
        # 热键输入框
        self.hotkey_entries: Dict[str, tk.Entry] = {}
        
        # 按键检测变量
        self.detecting_hotkey = False
        self.current_hotkey_detection = None
        self.pressed_keys = set()  # 当前按下的键集合
        self.modifier_keys = set()  # 修饰键集合
        
        # 显示设置控件
        self.show_status_var: Optional[tk.BooleanVar] = None
        self.status_x_var: Optional[tk.StringVar] = None
        self.status_y_var: Optional[tk.StringVar] = None
        
        # 热键监听回调
        self.hotkey_callback: Optional[Callable[[str, str], None]] = None
        
        logging.info("设置对话框初始化完成")
    
    def show(self):
        """
        显示设置对话框
        """
        # 如果对话框已经存在，则显示它
        if self.dialog and self.dialog.winfo_exists():
            self.dialog.lift()
            self.dialog.focus_force()
            return
        
        # 创建对话框窗口
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("钓鱼脚本设置")
        self.dialog.geometry("550x500")  # 增加尺寸
        self.dialog.resizable(True, True)  # 允许调整大小
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # 设置窗口图标
        try:
            self.dialog.iconbitmap("assets/icons/settings.ico")
        except:
            pass
        
        # 创建选项卡
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 热键设置选项卡
        hotkey_frame = ttk.Frame(notebook)
        notebook.add(hotkey_frame, text="热键设置")
        self._create_hotkey_settings(hotkey_frame)
        
        # 显示设置选项卡
        display_frame = ttk.Frame(notebook)
        notebook.add(display_frame, text="显示设置")
        self._create_display_settings(display_frame)
        
        # 高级设置选项卡
        advanced_frame = ttk.Frame(notebook)
        notebook.add(advanced_frame, text="高级设置")
        self._create_advanced_settings(advanced_frame)
        
        # 底部按钮
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(btn_frame, text="保存", command=self._save_settings).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="取消", command=self._close_dialog).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="应用", command=self._apply_settings).pack(side="right", padx=5)
        
        # 设置对话框关闭事件
        self.dialog.protocol("WM_DELETE_WINDOW", self._close_dialog)
        
        # 加载当前设置
        self._load_current_settings()
        
        # 按键监听
        self.dialog.bind('<KeyPress>', self._on_key_press)
        self.dialog.bind('<KeyRelease>', self._on_key_release)
        
        logging.info("设置对话框已显示")
    
    def _create_hotkey_settings(self, parent):
        """
        创建热键设置界面
        
        Args:
            parent: 父容器
        """
        # 获取当前热键设置
        hotkeys = self.config_manager.get_hotkeys()
        
        # 创建热键设置框架
        frame = ttk.LabelFrame(parent, text="快捷键设置")
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 添加说明
        instruction = ttk.Label(frame, text="点击按钮开始检测热键，然后按下您想设置的按键组合。",
                              wraplength=400, justify="left")
        instruction.grid(row=0, column=0, columnspan=2, padx=5, pady=10, sticky="w")
        
        # 开始钓鱼热键
        ttk.Label(frame, text="开始钓鱼:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        # 热键显示框架
        start_frame = ttk.Frame(frame)
        start_frame.grid(row=1, column=1, padx=5, pady=5, sticky="we")
        
        # 热键显示标签
        self.start_hotkey_label = ttk.Label(
            start_frame, 
            text=hotkeys.get('start', "Ctrl+Alt+F"),
            width=15,
            background="#f0f0f0",
            foreground="#e74c3c",
            relief=tk.SUNKEN,
            padding=5
        )
        self.start_hotkey_label.pack(side="left", padx=(0, 5))
        
        # 检测按钮
        self.start_detect_btn = ttk.Button(
            start_frame, 
            text="点击检测", 
            command=lambda: self._start_hotkey_detection('start')
        )
        self.start_detect_btn.pack(side="left")
        
        # 结束钓鱼热键
        ttk.Label(frame, text="结束钓鱼:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        
        # 热键显示框架
        stop_frame = ttk.Frame(frame)
        stop_frame.grid(row=2, column=1, padx=5, pady=5, sticky="we")
        
        # 热键显示标签
        self.stop_hotkey_label = ttk.Label(
            stop_frame, 
            text=hotkeys.get('stop', "Ctrl+Alt+Q"),
            width=15,
            background="#f0f0f0",
            foreground="#e74c3c",
            relief=tk.SUNKEN,
            padding=5
        )
        self.stop_hotkey_label.pack(side="left", padx=(0, 5))
        
        # 检测按钮
        self.stop_detect_btn = ttk.Button(
            stop_frame, 
            text="点击检测", 
            command=lambda: self._start_hotkey_detection('stop')
        )
        self.stop_detect_btn.pack(side="left")
        
        # 热键提示状态标签
        self.hotkey_status_label = ttk.Label(frame, text="", foreground="#3498db")
        self.hotkey_status_label.grid(row=3, column=0, columnspan=2, padx=5, pady=10, sticky="w")
        
        # 设置列权重
        frame.columnconfigure(1, weight=1)
    
    def _create_display_settings(self, parent):
        """
        创建显示设置界面
        
        Args:
            parent: 父容器
        """
        # 获取当前显示设置
        display_config = self.config_manager.get_display_config()
        
        # 创建显示设置框架
        frame = ttk.LabelFrame(parent, text="状态显示设置")
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 是否显示状态
        self.show_status_var = tk.BooleanVar(value=display_config.get('show_status', True))
        ttk.Checkbutton(
            frame, 
            text="在屏幕上显示当前识别的状态", 
            variable=self.show_status_var
        ).grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        # 显示位置
        ttk.Label(frame, text="显示位置:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        pos_frame = ttk.Frame(frame)
        pos_frame.grid(row=1, column=1, padx=5, pady=5, sticky="we")
        
        ttk.Label(pos_frame, text="X:").pack(side="left", padx=2)
        self.status_x_var = tk.StringVar(value=str(display_config['status_position']['x']))
        ttk.Entry(pos_frame, width=5, textvariable=self.status_x_var).pack(side="left", padx=2)
        
        ttk.Label(pos_frame, text="Y:").pack(side="left", padx=10)
        self.status_y_var = tk.StringVar(value=str(display_config['status_position']['y']))
        ttk.Entry(pos_frame, width=5, textvariable=self.status_y_var).pack(side="left", padx=2)
        
        # 设置列权重
        frame.columnconfigure(1, weight=1)
    
    def _create_advanced_settings(self, parent):
        """
        创建高级设置界面
        
        Args:
            parent: 父容器
        """
        # 创建高级设置框架
        frame = ttk.LabelFrame(parent, text="高级设置")
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 获取当前模型配置
        model_config = self.config_manager.get_config('model')
        
        # 模型置信度阈值
        ttk.Label(frame, text="检测置信度阈值:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.confidence_var = tk.StringVar(value=str(model_config.get('confidence', 0.7)))
        confidence_entry = ttk.Entry(frame, textvariable=self.confidence_var, width=8)
        confidence_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(frame, text="(推荐值: 0.7)").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        # 检测帧率
        ttk.Label(frame, text="检测帧率:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.fps_var = tk.StringVar(value=str(model_config.get('fps', 10)))
        fps_entry = ttk.Entry(frame, textvariable=self.fps_var, width=8)
        fps_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(frame, text="(推荐值: 10)").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        
        # 获取钓鱼操作配置
        fishing_config = self.config_manager.get_config('fishing')
        
        # 点击减速系数
        ttk.Label(frame, text="点击减速系数:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.slowdown_var = tk.StringVar(value=str(fishing_config.get('click_slowdown_factor', 1.0)))
        slowdown_entry = ttk.Entry(frame, textvariable=self.slowdown_var, width=8)
        slowdown_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(frame, text="(推荐值: 1.0)").grid(row=2, column=2, padx=5, pady=5, sticky="w")
        
        # 重置按钮
        ttk.Button(frame, text="恢复默认值", command=self._reset_advanced_settings).grid(
            row=3, column=0, columnspan=3, padx=5, pady=15)
        
        # 帮助说明
        ttk.Label(
            frame, 
            text="注意: 高级设置可能会影响脚本的稳定性，除非你知道自己在做什么，否则不建议修改。",
            wraplength=380
        ).grid(row=4, column=0, columnspan=3, padx=5, pady=10, sticky="w")
        
        # 设置列权重
        frame.columnconfigure(1, weight=1)
    
    def _reset_advanced_settings(self):
        """重置高级设置为默认值"""
        self.confidence_var.set("0.7")
        self.fps_var.set("10")
        self.slowdown_var.set("1.0")
        messagebox.showinfo("提示", "高级设置已恢复默认值")
    
    def _load_current_settings(self):
        """
        加载当前设置
        """
        # 已在初始化时加载
        pass
    
    def _start_hotkey_detection(self, hotkey_type):
        """
        开始热键检测
        
        Args:
            hotkey_type: 热键类型
        """
        # 如果已经在检测，先取消当前检测
        if self.detecting_hotkey:
            self._cancel_hotkey_detection()
            # 如果用户点击了同一个按钮，则只是取消检测
            if self.current_hotkey_detection == hotkey_type:
                return
        
        # 设置当前检测热键类型
        self.detecting_hotkey = True
        self.current_hotkey_detection = hotkey_type
        
        # 更新状态标签
        self.hotkey_status_label.config(text="请按下您想设置的按键组合...", foreground="#e67e22")
        
        # 更新检测按钮
        if hotkey_type == 'start':
            self.start_detect_btn.config(text="取消检测")
            self.start_hotkey_label.config(text="检测中...")
        else:
            self.stop_detect_btn.config(text="取消检测")
            self.stop_hotkey_label.config(text="检测中...")
        
        # 聚焦对话框
        self.dialog.focus_force()
    
    def _cancel_hotkey_detection(self):
        """取消热键检测"""
        current_type = self.current_hotkey_detection
        self.detecting_hotkey = False
        self.current_hotkey_detection = None
        
        # 清空按键状态
        self.pressed_keys.clear()
        self.modifier_keys.clear()
        
        # 恢复按钮状态
        self.start_detect_btn.config(text="点击检测")
        self.stop_detect_btn.config(text="点击检测")
        
        # 如果是用户手动取消，则恢复原热键显示
        if current_type:
            hotkeys = self.config_manager.get_hotkeys()
            if current_type == 'start':
                self.start_hotkey_label.config(text=hotkeys.get('start', "Ctrl+Alt+F"))
            else:
                self.stop_hotkey_label.config(text=hotkeys.get('stop', "Ctrl+Alt+Q"))
    
    def _on_key_press(self, event):
        """处理按键按下事件"""
        if not self.detecting_hotkey:
            return
            
        # 获取按下的键
        key = event.keysym.lower()
        
        # 记录按下的键
        self.pressed_keys.add(key)
        
        # 识别修饰键
        if key in ['control_l', 'control_r']:
            self.modifier_keys.add('ctrl')
        elif key in ['alt_l', 'alt_r']:
            self.modifier_keys.add('alt')
        elif key in ['shift_l', 'shift_r']:
            self.modifier_keys.add('shift')
        elif key in ['win_l', 'win_r', 'super_l', 'super_r']:
            self.modifier_keys.add('win')
        else:
            # 主键，触发热键处理
            self._process_hotkey_combination(key)
    
    def _on_key_release(self, event):
        """处理按键释放事件"""
        if not self.detecting_hotkey:
            return
        
        # 获取释放的键
        key = event.keysym.lower()
        
        # 从按下的键集合中移除
        self.pressed_keys.discard(key)
        
        # 移除修饰键
        if key in ['control_l', 'control_r']:
            self.modifier_keys.discard('ctrl')
        elif key in ['alt_l', 'alt_r']:
            self.modifier_keys.discard('alt')
        elif key in ['shift_l', 'shift_r']:
            self.modifier_keys.discard('shift')
        elif key in ['win_l', 'win_r', 'super_l', 'super_r']:
            self.modifier_keys.discard('win')
    
    def _process_hotkey_combination(self, main_key):
        """处理热键组合"""
        # 构建热键组合
        hotkey_parts = list(self.modifier_keys.copy())  # 复制修饰键
        
        # 处理主键
        if main_key == 'space':
            hotkey_parts.append('space')
        elif main_key == 'return':
            hotkey_parts.append('enter')
        elif main_key == 'tab':
            hotkey_parts.append('tab')
        elif main_key == 'escape':
            hotkey_parts.append('esc')
        elif main_key.startswith('f') and len(main_key) > 1 and main_key[1:].isdigit():
            hotkey_parts.append(main_key)
        elif len(main_key) == 1 and main_key.isalnum():
            hotkey_parts.append(main_key)
        elif main_key in ['up', 'down', 'left', 'right']:
            hotkey_parts.append(main_key)
        elif main_key in ['home', 'end', 'page_up', 'page_down', 'insert', 'delete']:
            hotkey_parts.append(main_key)
        else:
            # 不支持的键
            self.hotkey_status_label.config(text=f"不支持的按键: {main_key}，请重试", foreground="#e74c3c")
            self._cancel_hotkey_detection()
            return
        
        # 构建热键字符串（按标准顺序：ctrl+alt+shift+key）
        ordered_parts = []
        if 'ctrl' in hotkey_parts:
            ordered_parts.append('ctrl')
        if 'alt' in hotkey_parts:
            ordered_parts.append('alt')
        if 'shift' in hotkey_parts:
            ordered_parts.append('shift')
        if 'win' in hotkey_parts:
            ordered_parts.append('win')
        
        # 添加主键（非修饰键）
        for part in hotkey_parts:
            if part not in ['ctrl', 'alt', 'shift', 'win']:
                ordered_parts.append(part)
        
        # 检查热键有效性
        if not ordered_parts or all(part in ['ctrl', 'alt', 'shift', 'win'] for part in ordered_parts):
            self.hotkey_status_label.config(text="无效的热键组合，需要至少一个非修饰键", foreground="#e74c3c")
            self._cancel_hotkey_detection()
            return
        
        # 组合热键
        hotkey = '+'.join(ordered_parts)
        
        # 更新热键
        if self.current_hotkey_detection == 'start':
            self.start_hotkey_label.config(text=hotkey)
        else:
            self.stop_hotkey_label.config(text=hotkey)
        
        # 保存热键
        self.config_manager.update_config('hotkeys', self.current_hotkey_detection, hotkey)
        
        # 通知热键变更
        if self.hotkey_callback:
            self.hotkey_callback(self.current_hotkey_detection, hotkey)
        
        # 更新状态
        self.hotkey_status_label.config(text=f"热键已设置为: {hotkey}", foreground="#2ecc71")
        
        # 完成检测
        self._cancel_hotkey_detection()
    
    def _apply_settings(self, show_message=True):
        """
        应用设置
        
        Args:
            show_message: 是否显示提示消息
        
        Returns:
            bool: 是否应用成功
        """
        try:
            # 更新显示设置
            show_status = self.show_status_var.get()
            self.config_manager.update_config('display', 'show_status', show_status)
            self.status_display.set_visibility(show_status)
            
            try:
                x = int(self.status_x_var.get())
                y = int(self.status_y_var.get())
                self.config_manager.update_config('display', 'status_position', {'x': x, 'y': y})
                self.status_display.set_position(x, y)
            except ValueError:
                messagebox.showerror("输入错误", "状态显示位置必须是整数")
                return False
            
            # 更新高级设置
            try:
                confidence = float(self.confidence_var.get())
                if not (0.0 <= confidence <= 1.0):
                    raise ValueError("置信度阈值必须在0到1之间")
                self.config_manager.update_config('model', 'confidence', confidence)
            except ValueError as e:
                messagebox.showerror("输入错误", f"置信度阈值错误: {str(e)}")
                return False
            
            try:
                fps = float(self.fps_var.get())
                if not (1.0 <= fps <= 60.0):
                    raise ValueError("帧率必须在1到60之间")
                self.config_manager.update_config('model', 'fps', fps)
            except ValueError as e:
                messagebox.showerror("输入错误", f"帧率错误: {str(e)}")
                return False
            
            try:
                slowdown = float(self.slowdown_var.get())
                if slowdown <= 0:
                    raise ValueError("减速系数必须大于0")
                self.config_manager.update_config('fishing', 'click_slowdown_factor', slowdown)
            except ValueError as e:
                messagebox.showerror("输入错误", f"减速系数错误: {str(e)}")
                return False
            
            logging.info("设置已应用")
            
            # 仅在需要时显示成功提示
            if show_message:
                messagebox.showinfo("成功", "设置已应用")
                
            return True
            
        except Exception as e:
            logging.error(f"应用设置时出错: {str(e)}")
            messagebox.showerror("错误", f"应用设置时出错: {str(e)}")
            return False
    
    def _save_settings(self):
        """
        保存设置
        """
        try:
            # 先应用设置，但不显示提示
            result = self._apply_settings(show_message=False)
            
            # 如果应用设置成功
            if result:
                # 保存到配置文件
                self.config_manager.save_config()
                logging.info("设置已保存到配置文件")
                
                # 关闭对话框，不显示提示
                self._close_dialog()
        except Exception as e:
            logging.error(f"保存设置到配置文件时出错: {str(e)}")
            messagebox.showerror("错误", f"保存设置到配置文件时出错: {str(e)}")
    
    def _close_dialog(self):
        """
        关闭对话框
        """
        if self.dialog:
            self.dialog.destroy()
            self.dialog = None
    
    def set_hotkey_callback(self, callback: Callable[[str, str], None]):
        """
        设置热键变更回调函数
        
        Args:
            callback: 回调函数，接收热键名称和新值
        """
        self.hotkey_callback = callback 