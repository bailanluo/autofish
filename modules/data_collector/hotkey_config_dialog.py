"""
热键配置对话框模块
提供按键检测和热键配置功能
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Optional
import sys
import os

# 添加主项目路径以使用logger
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from modules.logger import setup_logger


class HotkeyDetectionDialog:
    """热键检测对话框 - 使用按键检测而不是文本输入"""
    
    def __init__(self, parent, current_hotkeys: Dict[str, str], auto_save_callback=None):
        """初始化热键检测对话框"""
        self.result = None  # 配置结果
        self.detecting = False  # 是否正在检测按键
        self.current_hotkey_type = None  # 当前正在设置的热键类型
        self.pressed_keys = set()  # 当前按下的键集合
        self.modifier_keys = set()  # 修饰键集合
        self._main_app_callback = auto_save_callback  # 自动保存回调
        
        # 当前热键配置
        self.current_hotkeys = {
            'select_region': current_hotkeys.get('select_region', 'ctrl+alt+y'),
            'quick_capture': current_hotkeys.get('quick_capture', 'y'),
            'pause_capture': current_hotkeys.get('pause_capture', 'ctrl+alt+p')
        }
        
        # 初始化配置管理器
        try:
            from .config_manager import DataCollectorConfig
            self.config_manager = DataCollectorConfig()
        except Exception as e:
            print(f"初始化配置管理器失败: {e}")
            self.config_manager = None
        
        # 创建对话框窗口
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("热键配置")
        self.dialog.geometry("650x650")  # 增加高度以容纳新的系统设置
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(True, True)
        
        # 居中显示
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        x = parent_x + (parent_width - 650) // 2
        y = parent_y + (parent_height - 650) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        # 监听键盘事件 - 同时监听按下和释放
        self.dialog.bind('<KeyPress>', self.on_key_press)
        self.dialog.bind('<KeyRelease>', self.on_key_release)
        self.dialog.focus_set()
        
        self._create_widgets()
        
        # 等待用户操作
        self.dialog.wait_window()
    
    def _create_widgets(self):
        """创建界面控件"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="🎮 热键配置", 
                               font=('Microsoft YaHei', 16, 'bold'),
                               foreground="#2c3e50")
        title_label.pack(pady=(0, 20))
        
        # 说明文本
        instruction_frame = ttk.LabelFrame(main_frame, text="操作说明", padding="15")
        instruction_frame.pack(fill=tk.X, pady=(0, 20))
        
        instruction_text = """💡 点击下方按钮开始检测，然后按下你想要设置的热键组合
⌨️ 支持的热键：单键(如Y)、组合键(如Ctrl+Alt+Y)
🔄 点击"重置默认"可恢复到初始设置
✨ 设置成功后会自动保存并应用！"""
        
        instruction_label = ttk.Label(instruction_frame, text=instruction_text, 
                                     font=('Microsoft YaHei', 9),
                                     foreground="#34495e")
        instruction_label.pack()
        
        # 热键设置区域
        hotkeys_frame = ttk.LabelFrame(main_frame, text="热键设置", padding="15")
        hotkeys_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 选择区域热键
        region_frame = ttk.Frame(hotkeys_frame)
        region_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(region_frame, text="📋 选择区域热键:", 
                 font=('Microsoft YaHei', 10, 'bold')).pack(side=tk.LEFT)
        
        self.region_display = ttk.Label(region_frame, 
                                       text=self._format_hotkey_display(self.current_hotkeys['select_region']),
                                       font=('Consolas', 10, 'bold'),
                                       foreground="#e74c3c",
                                       background="#ecf0f1",
                                       relief=tk.RAISED,
                                       padding="5")
        self.region_display.pack(side=tk.RIGHT)
        
        self.region_button = ttk.Button(region_frame, text="🎯 点击检测",
                                       command=lambda: self._start_detection('select_region'))
        self.region_button.pack(side=tk.RIGHT, padx=(10, 10))
        
        # 快速截图热键
        capture_frame = ttk.Frame(hotkeys_frame)
        capture_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(capture_frame, text="📸 快速截图热键:", 
                 font=('Microsoft YaHei', 10, 'bold')).pack(side=tk.LEFT)
        
        self.capture_display = ttk.Label(capture_frame,
                                        text=self._format_hotkey_display(self.current_hotkeys['quick_capture']),
                                        font=('Consolas', 10, 'bold'),
                                        foreground="#e74c3c",
                                        background="#ecf0f1",
                                        relief=tk.RAISED,
                                        padding="5")
        self.capture_display.pack(side=tk.RIGHT)
        
        self.capture_button = ttk.Button(capture_frame, text="🎯 点击检测",
                                        command=lambda: self._start_detection('quick_capture'))
        self.capture_button.pack(side=tk.RIGHT, padx=(10, 10))
        
        # 暂停功能热键
        pause_frame = ttk.Frame(hotkeys_frame)
        pause_frame.pack(fill=tk.X)
        
        ttk.Label(pause_frame, text="⏸️ 暂停截图热键:", 
                 font=('Microsoft YaHei', 10, 'bold')).pack(side=tk.LEFT)
        
        self.pause_display = ttk.Label(pause_frame,
                                      text=self._format_hotkey_display(self.current_hotkeys['pause_capture']),
                                      font=('Consolas', 10, 'bold'),
                                      foreground="#e74c3c",
                                      background="#ecf0f1",
                                      relief=tk.RAISED,
                                      padding="5")
        self.pause_display.pack(side=tk.RIGHT)
        
        self.pause_button = ttk.Button(pause_frame, text="🎯 点击检测",
                                      command=lambda: self._start_detection('pause_capture'))
        self.pause_button.pack(side=tk.RIGHT, padx=(10, 10))
        
        # 系统设置区域
        system_frame = ttk.LabelFrame(main_frame, text="系统设置", padding="15")
        system_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 管理员启动选项
        admin_frame = ttk.Frame(system_frame)
        admin_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 获取当前管理员设置状态
        current_admin_setting = True  # 默认值
        if self.config_manager:
            try:
                current_admin_setting = self.config_manager.get_run_as_admin()
            except:
                current_admin_setting = True
        
        self.run_as_admin_var = tk.BooleanVar(value=current_admin_setting)
        
        admin_checkbox = ttk.Checkbutton(
            admin_frame,
            text="默认以管理员身份启动程序",
            variable=self.run_as_admin_var,
            command=self._on_admin_setting_changed
        )
        admin_checkbox.pack(side=tk.LEFT)
        
        # 管理员设置说明
        admin_info = ttk.Label(
            system_frame,
            text="💡 启用后程序会自动请求管理员权限，确保全局热键功能正常工作",
            font=('Microsoft YaHei', 9),
            foreground="#7f8c8d"
        )
        admin_info.pack(fill=tk.X)
        
        # 自动保存热键设置
        autosave_frame = ttk.Frame(system_frame)
        autosave_frame.pack(fill=tk.X, pady=(15, 0))
        
        # 获取当前自动保存设置状态
        current_autosave_setting = True  # 默认值
        if self.config_manager:
            try:
                current_autosave_setting = self.config_manager.get_auto_save_hotkeys()
            except:
                current_autosave_setting = True
        
        self.auto_save_hotkeys_var = tk.BooleanVar(value=current_autosave_setting)
        
        autosave_checkbox = ttk.Checkbutton(
            autosave_frame,
            text="自动保存热键设置",
            variable=self.auto_save_hotkeys_var,
            command=self._on_autosave_setting_changed
        )
        autosave_checkbox.pack(side=tk.LEFT)
        
        # 自动保存设置说明
        autosave_info = ttk.Label(
            system_frame,
            text="💡 启用后热键设置会立即保存并生效，无需手动保存",
            font=('Microsoft YaHei', 9),
            foreground="#7f8c8d"
        )
        autosave_info.pack(fill=tk.X, pady=(5, 0))
        
        # 状态显示
        self.status_label = ttk.Label(main_frame, text="准备就绪",
                                     font=('Microsoft YaHei', 10),
                                     foreground="#27ae60")
        self.status_label.pack(pady=10)
        
        # 按钮区域 - 只保留重置按钮，因为现在是自动保存
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(30, 10))
        
        # 添加分隔线
        ttk.Separator(button_frame, orient='horizontal').pack(fill=tk.X, pady=(0, 15))
        
        # 按钮容器
        buttons_container = ttk.Frame(button_frame)
        buttons_container.pack()
        
        # 重置按钮居中显示
        reset_btn = ttk.Button(buttons_container, text="🔄 重置默认", 
                              command=self._reset_defaults)
        reset_btn.pack(padx=10)
        
        # 添加自动保存提示
        auto_save_label = ttk.Label(main_frame, 
                                   text="💡 热键设置会自动保存并立即生效", 
                                   font=('Microsoft YaHei', 9),
                                   foreground="#27ae60")
        auto_save_label.pack(pady=(10, 0))
    
    def _format_hotkey_display(self, hotkey: str) -> str:
        """格式化热键显示"""
        if not hotkey:
            return "未设置"
        
        parts = hotkey.lower().split('+')
        display_parts = []
        
        for part in parts:
            if part == 'ctrl':
                display_parts.append('Ctrl')
            elif part == 'alt':
                display_parts.append('Alt')
            elif part == 'shift':
                display_parts.append('Shift')
            elif part == 'space':
                display_parts.append('Space')
            elif part == 'enter':
                display_parts.append('Enter')
            elif part.startswith('f') and part[1:].isdigit():
                display_parts.append(part.upper())
            else:
                display_parts.append(part.upper())
        
        return ' + '.join(display_parts)
    
    def _start_detection(self, hotkey_type: str):
        """开始检测热键"""
        self.detecting = True
        self.current_hotkey_type = hotkey_type
        
        # 更新状态
        if hotkey_type == 'select_region':
            self.status_label.config(text="🎯 请按下选择区域的热键组合...", foreground="#e67e22")
            self.region_button.config(text="🔴 检测中...", state=tk.DISABLED)
        elif hotkey_type == 'quick_capture':
            self.status_label.config(text="📸 请按下快速截图的热键组合...", foreground="#e67e22")
            self.capture_button.config(text="🔴 检测中...", state=tk.DISABLED)
        elif hotkey_type == 'pause_capture':
            self.status_label.config(text="⏸️ 请按下暂停截图的热键组合...", foreground="#e67e22")
            self.pause_button.config(text="🔴 检测中...", state=tk.DISABLED)
        
        # 禁用其他按钮
        for button in [self.region_button, self.capture_button, self.pause_button]:
            if (hotkey_type == 'select_region' and button != self.region_button) or \
               (hotkey_type == 'quick_capture' and button != self.capture_button) or \
               (hotkey_type == 'pause_capture' and button != self.pause_button):
                button.config(state=tk.DISABLED)
    
    def on_key_press(self, event):
        """处理按键按下事件"""
        if not self.detecting:
            return
        
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
            # 这是主键，触发热键检测
            self._process_hotkey_combination(key)
    
    def on_key_release(self, event):
        """处理按键释放事件"""
        if not self.detecting:
            return
        
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
    
    def _process_hotkey_combination(self, main_key: str):
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
            self.status_label.config(text=f"❌ 不支持的按键: {main_key}，请重试", foreground="#e74c3c")
            self._cancel_detection()
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
        
        hotkey_string = '+'.join(ordered_parts)
        
        # 检查热键有效性
        if not ordered_parts or all(part in ['ctrl', 'alt', 'shift', 'win'] for part in ordered_parts):
            self.status_label.config(text="❌ 无效的热键组合，需要至少一个非修饰键", foreground="#e74c3c")
            self._cancel_detection()
            return
        
        # 检查是否与现有热键冲突
        if self._check_hotkey_conflict(hotkey_string):
            self.status_label.config(text="⚠️ 热键冲突，请选择其他组合", foreground="#e67e22")
            self._cancel_detection()
            return
        
        # 更新热键配置
        self.current_hotkeys[self.current_hotkey_type] = hotkey_string
        
        # 更新显示
        if self.current_hotkey_type == 'select_region':
            self.region_display.config(text=self._format_hotkey_display(hotkey_string))
        elif self.current_hotkey_type == 'quick_capture':
            self.capture_display.config(text=self._format_hotkey_display(hotkey_string))
        elif self.current_hotkey_type == 'pause_capture':
            self.pause_display.config(text=self._format_hotkey_display(hotkey_string))
        
        # 完成检测并自动保存
        self.status_label.config(text=f"✅ 热键设置成功: {self._format_hotkey_display(hotkey_string)} (已自动保存)", 
                               foreground="#27ae60")
        
        # 自动保存配置
        self._auto_save_config()
        
        self._cancel_detection()
    
    def _check_hotkey_conflict(self, hotkey: str) -> bool:
        """检查热键冲突"""
        for existing_type, existing_hotkey in self.current_hotkeys.items():
            if existing_type != self.current_hotkey_type and existing_hotkey == hotkey:
                return True
        return False
    
    def _cancel_detection(self):
        """取消检测"""
        self.detecting = False
        self.current_hotkey_type = None
        
        # 清空按键状态
        self.pressed_keys.clear()
        self.modifier_keys.clear()
        
        # 恢复按钮状态
        self.region_button.config(text="🎯 点击检测", state=tk.NORMAL)
        self.capture_button.config(text="🎯 点击检测", state=tk.NORMAL)
        self.pause_button.config(text="🎯 点击检测", state=tk.NORMAL)
        
        # 延迟恢复状态文本
        self.dialog.after(2000, lambda: self.status_label.config(text="准备就绪", foreground="#27ae60"))
    
    def _reset_defaults(self):
        """重置为默认热键"""
        self.current_hotkeys = {
            'select_region': 'ctrl+alt+y',
            'quick_capture': 'y',
            'pause_capture': 'ctrl+alt+p'
        }
        
        # 更新显示
        self.region_display.config(text=self._format_hotkey_display(self.current_hotkeys['select_region']))
        self.capture_display.config(text=self._format_hotkey_display(self.current_hotkeys['quick_capture']))
        self.pause_display.config(text=self._format_hotkey_display(self.current_hotkeys['pause_capture']))
        
        self.status_label.config(text="🔄 已重置为默认热键", foreground="#3498db")
    
    def _auto_save_config(self):
        """自动保存配置（不关闭对话框）"""
        self.result = self.current_hotkeys.copy()
        
        # 直接调用主程序的配置更新方法（如果有的话）
        if hasattr(self, '_main_app_callback') and self._main_app_callback:
            try:
                self._main_app_callback(self.current_hotkeys.copy())
            except Exception as e:
                print(f"自动保存配置失败: {e}")
    
    def close_dialog(self):
        """关闭对话框"""
        self.result = self.current_hotkeys.copy()
        self.dialog.destroy()
    
    def _on_admin_setting_changed(self):
        """处理管理员启动选项的变化"""
        try:
            if self.config_manager:
                # 保存管理员设置
                new_value = self.run_as_admin_var.get()
                self.config_manager.set_run_as_admin(new_value)
                self.config_manager.save_config()
                
                # 更新状态显示
                if new_value:
                    self.status_label.config(text="✅ 已启用管理员启动 (已自动保存)", foreground="#27ae60")
                else:
                    self.status_label.config(text="⚠️ 已禁用管理员启动 (已自动保存)", foreground="#e67e22")
                
                # 延迟恢复状态文本
                self.dialog.after(3000, lambda: self.status_label.config(text="准备就绪", foreground="#27ae60"))
                
        except Exception as e:
            self.status_label.config(text=f"❌ 保存管理员设置失败: {e}", foreground="#e74c3c")
            self.dialog.after(3000, lambda: self.status_label.config(text="准备就绪", foreground="#27ae60"))

    def _on_autosave_setting_changed(self):
        """处理自动保存热键设置选项的变化"""
        try:
            if self.config_manager:
                # 保存自动保存设置
                new_value = self.auto_save_hotkeys_var.get()
                self.config_manager.set_auto_save_hotkeys(new_value)
                self.config_manager.save_config()
                
                # 更新状态显示
                if new_value:
                    self.status_label.config(text="✅ 已启用自动保存热键设置 (已自动保存)", foreground="#27ae60")
                else:
                    self.status_label.config(text="⚠️ 已禁用自动保存热键设置 (已自动保存)", foreground="#e67e22")
                
                # 延迟恢复状态文本
                self.dialog.after(3000, lambda: self.status_label.config(text="准备就绪", foreground="#27ae60"))
                
        except Exception as e:
            self.status_label.config(text=f"❌ 保存自动保存设置失败: {e}", foreground="#e74c3c")
            self.dialog.after(3000, lambda: self.status_label.config(text="准备就绪", foreground="#27ae60")) 