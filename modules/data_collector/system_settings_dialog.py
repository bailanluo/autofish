"""
系统设置对话框模块
提供系统级配置选项，如管理员启动等
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Callable
import sys
import os

# 添加主项目路径以使用logger
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from modules.logger import setup_logger

try:
    from .admin_utils import is_admin, get_admin_status_message
    from .config_manager import DataCollectorConfig
except ImportError:
    from admin_utils import is_admin, get_admin_status_message
    from config_manager import DataCollectorConfig


class SystemSettingsDialog:
    """系统设置对话框"""
    
    def __init__(self, parent, config_manager: DataCollectorConfig, save_callback: Callable = None):
        """
        初始化系统设置对话框
        
        Args:
            parent: 父窗口
            config_manager: 配置管理器
            save_callback: 保存后的回调函数
        """
        self.parent = parent
        self.config_manager = config_manager
        self.save_callback = save_callback
        self.result = None  # 对话框结果
        
        # 创建对话框变量 - 移除管理员启动选项
        self.auto_save_hotkeys_var = tk.BooleanVar()
        
        # 创建对话框窗口
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("系统设置")
        self.dialog.geometry("550x400")  # 减小高度，因为移除了管理员选项
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        
        # 居中显示
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        x = parent_x + (parent_width - 550) // 2
        y = parent_y + (parent_height - 400) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        # 加载当前配置
        self._load_current_config()
        
        # 创建界面
        self._create_widgets()
        
        # 等待用户操作
        self.dialog.wait_window()
    
    def _load_current_config(self):
        """加载当前配置"""
        self.auto_save_hotkeys_var.set(self.config_manager.get_auto_save_hotkeys())
    
    def _create_widgets(self):
        """创建界面控件"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="🔧 系统设置", 
                               font=('Microsoft YaHei', 16, 'bold'),
                               foreground="#2c3e50")
        title_label.pack(pady=(0, 20))
        
        # 应用程序设置区域
        self._create_app_settings(main_frame)
        
        # 状态信息区域
        self._create_status_info(main_frame)
        
        # 按钮区域
        self._create_buttons(main_frame)
    
    def _create_app_settings(self, parent):
        """创建应用程序设置区域"""
        app_frame = ttk.LabelFrame(parent, text="应用程序设置", padding="15")
        app_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 自动保存热键设置
        hotkey_frame = ttk.Frame(app_frame)
        hotkey_frame.pack(fill=tk.X, pady=(0, 10))
        
        hotkey_checkbox = ttk.Checkbutton(
            hotkey_frame,
            text="自动保存热键设置",
            variable=self.auto_save_hotkeys_var
        )
        hotkey_checkbox.pack(side=tk.LEFT)
        
        # 自动保存说明
        hotkey_info = ttk.Label(
            app_frame,
            text="💡 启用后热键设置会立即保存并生效，无需手动保存",
            font=('Microsoft YaHei', 9),
            foreground="#7f8c8d"
        )
        hotkey_info.pack(fill=tk.X)
    
    def _create_status_info(self, parent):
        """创建状态信息区域"""
        status_frame = ttk.LabelFrame(parent, text="系统信息", padding="15")
        status_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 系统信息
        info_text = f"""
🖥️ 操作系统: Windows
🐍 Python版本: {sys.version.split()[0]}
📁 程序路径: {os.path.abspath(sys.argv[0])}
⚙️ 配置文件: {self.config_manager.config_path}
        """.strip()
        
        info_label = ttk.Label(
            status_frame,
            text=info_text,
            font=('Consolas', 9),
            foreground="#34495e"
        )
        info_label.pack(fill=tk.X)
    
    def _create_buttons(self, parent):
        """创建按钮区域"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        # 添加分隔线
        ttk.Separator(button_frame, orient='horizontal').pack(fill=tk.X, pady=(0, 15))
        
        # 按钮容器
        buttons_container = ttk.Frame(button_frame)
        buttons_container.pack()
        
        # 保存按钮
        save_btn = ttk.Button(
            buttons_container,
            text="💾 保存设置",
            command=self._save_settings
        )
        save_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 取消按钮
        cancel_btn = ttk.Button(
            buttons_container,
            text="❌ 取消",
            command=self._cancel
        )
        cancel_btn.pack(side=tk.LEFT)
        
        # 应用按钮样式
        style = ttk.Style()
        style.configure('Save.TButton', font=('Microsoft YaHei', 9, 'bold'))
        save_btn.configure(style='Save.TButton')
    
    def _save_settings(self):
        """保存设置"""
        try:
            # 保存配置
            self.config_manager.set('system.auto_save_hotkeys', self.auto_save_hotkeys_var.get())
            
            # 保存到文件
            if self.config_manager.save_config():
                print("系统设置已保存")
                
                # 调用回调函数
                if self.save_callback:
                    self.save_callback()
                
                print("系统设置已保存！")  # 简化显示，不弹窗
                self.dialog.destroy()
            else:
                print("无法保存系统设置，请检查文件权限。")
                
        except Exception as e:
            print(f"保存系统设置失败: {e}")
    
    def _cancel(self):
        """取消设置"""
        self.dialog.destroy() 