#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AutoFish UI界面模块

提供钓鱼程序的图形化用户界面。
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
from typing import Optional

from modules.auto_fisher.config import get_config
from modules.auto_fisher.fishing_controller import get_fishing_controller, FishingState
from modules.logger import setup_logger


class StatusWindow:
    """状态显示窗口"""
    
    def __init__(self):
        """初始化状态窗口"""
        self.config = get_config()
        self.window: Optional[tk.Toplevel] = None
        self.status_label: Optional[tk.Label] = None
        self.visible = False
    
    def create_window(self, parent: tk.Tk):
        """创建状态窗口"""
        if self.window:
            return
        
        self.window = tk.Toplevel(parent)
        self.window.title("钓鱼状态")
        self.window.geometry("200x60")
        self.window.overrideredirect(True)  # 无边框
        self.window.attributes('-topmost', True)  # 置顶
        
        # 设置透明度
        alpha = self.config.get('ui.status_window_alpha', 0.8)
        self.window.attributes('-alpha', alpha)
        
        # 设置位置
        pos = self.config.get('ui.status_window_position', [10, 10])
        self.window.geometry(f"+{pos[0]}+{pos[1]}")
        
        # 创建标签
        self.status_label = tk.Label(
            self.window,
            text="空闲状态",
            font=("Arial", 12, "bold"),
            fg="blue",
            bg="white",
            padx=10,
            pady=5
        )
        self.status_label.pack(fill=tk.BOTH, expand=True)
        
        # 隐藏窗口
        self.window.withdraw()
    
    def show(self):
        """显示状态窗口"""
        if self.window and not self.visible:
            self.window.deiconify()
            self.visible = True
    
    def hide(self):
        """隐藏状态窗口"""
        if self.window and self.visible:
            self.window.withdraw()
            self.visible = False
    
    def update_status(self, state: FishingState):
        """更新状态显示"""
        if not self.status_label:
            return
        
        # 状态名称映射
        state_names = {
            FishingState.IDLE: "空闲状态",
            FishingState.WAITING: "等待上钩",
            FishingState.FISH_HOOKED: "鱼已上钩",
            FishingState.PULLING_NORMAL: "正在提线",
            FishingState.PULLING_HALFWAY: "耐力不足",
            FishingState.PULL_RIGHT: "向右拉",
            FishingState.PULL_LEFT: "向左拉",
            FishingState.SUCCESS: "钓鱼成功"
        }
        
        status_text = state_names.get(state, f"状态{state.value}")
        self.status_label.config(text=status_text)
    
    def destroy(self):
        """销毁窗口"""
        if self.window:
            self.window.destroy()
            self.window = None
            self.status_label = None
            self.visible = False


class SettingsDialog:
    """设置对话框"""
    
    def __init__(self, parent: tk.Tk):
        """初始化设置对话框"""
        self.parent = parent
        self.config = get_config()
        self.dialog: Optional[tk.Toplevel] = None
        
        # 设置变量
        self.show_status_var = tk.BooleanVar()
        self.start_key_var = tk.StringVar()
        self.stop_key_var = tk.StringVar()
        self.pause_key_var = tk.StringVar()
    
    def show(self):
        """显示设置对话框"""
        if self.dialog:
            self.dialog.lift()
            return
        
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("设置")
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 50,
            self.parent.winfo_rooty() + 50
        ))
        
        self._create_widgets()
        self._load_settings()
        
        # 绑定关闭事件
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _create_widgets(self):
        """创建控件"""
        # 主框架
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 界面设置组
        ui_group = ttk.LabelFrame(main_frame, text="界面设置", padding="10")
        ui_group.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Checkbutton(
            ui_group,
            text="显示状态窗口",
            variable=self.show_status_var
        ).pack(anchor=tk.W)
        
        # 快捷键设置组
        hotkey_group = ttk.LabelFrame(main_frame, text="快捷键设置", padding="10")
        hotkey_group.pack(fill=tk.X, pady=(0, 10))
        
        # 开始快捷键
        ttk.Label(hotkey_group, text="开始钓鱼:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Entry(hotkey_group, textvariable=self.start_key_var, width=10).grid(row=0, column=1, sticky=tk.W)
        
        # 停止快捷键
        ttk.Label(hotkey_group, text="停止钓鱼:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        ttk.Entry(hotkey_group, textvariable=self.stop_key_var, width=10).grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        
        # 暂停快捷键
        ttk.Label(hotkey_group, text="暂停钓鱼:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        ttk.Entry(hotkey_group, textvariable=self.pause_key_var, width=10).grid(row=2, column=1, sticky=tk.W, pady=(5, 0))
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            button_frame,
            text="保存",
            command=self._save_settings
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(
            button_frame,
            text="取消",
            command=self._on_close
        ).pack(side=tk.RIGHT)
    
    def _load_settings(self):
        """加载设置"""
        # 界面设置
        show_status = self.config.get('ui.show_status_window', True)
        self.show_status_var.set(show_status)
        
        # 快捷键设置
        hotkeys = self.config.get_hotkeys()
        self.start_key_var.set(hotkeys.get('start', 'F1'))
        self.stop_key_var.set(hotkeys.get('stop', 'F2'))
        self.pause_key_var.set(hotkeys.get('pause', 'F3'))
    
    def _save_settings(self):
        """保存设置"""
        try:
            # 保存界面设置
            self.config.set('ui.show_status_window', self.show_status_var.get())
            
            # 保存快捷键设置
            self.config.set_hotkey('start', self.start_key_var.get())
            self.config.set_hotkey('stop', self.stop_key_var.get())
            self.config.set_hotkey('pause', self.pause_key_var.get())
            
            messagebox.showinfo("设置", "设置已保存")
            self._on_close()
            
        except Exception as e:
            logging.error(f"保存设置失败: {e}")
            messagebox.showerror("错误", f"保存设置失败: {e}")
    
    def _on_close(self):
        """关闭对话框"""
        if self.dialog:
            self.dialog.destroy()
            self.dialog = None


class FishingUI:
    """钓鱼主界面"""
    
    def __init__(self):
        """初始化主界面"""
        self.config = get_config()
        self.fishing_controller = get_fishing_controller()
        
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("AutoFish - 智能钓鱼助手 v2.4")
        self.root.geometry("500x380")
        self.root.resizable(True, True)
        self.root.minsize(450, 350)
        
        # 居中显示
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - self.root.winfo_width()) // 2
        y = (self.root.winfo_screenheight() - self.root.winfo_height()) // 2
        self.root.geometry(f"+{x}+{y}")
        
        # 子窗口
        self.status_window = StatusWindow()
        self.settings_dialog: Optional[SettingsDialog] = None
        
        # 创建界面
        self._create_widgets()
        
        # 设置状态回调
        self.fishing_controller.set_state_callback(self._on_state_changed)
        
        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        logging.info("钓鱼UI界面初始化完成")
    
    def _create_widgets(self):
        """创建控件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(
            main_frame,
            text="AutoFish 智能钓鱼助手",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # 状态显示
        self.status_label = ttk.Label(
            main_frame,
            text="状态: 空闲",
            font=("Arial", 12)
        )
        self.status_label.pack(pady=(0, 20))
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(0, 20))
        
        # 开始按钮
        self.start_button = ttk.Button(
            button_frame,
            text="开始钓鱼",
            command=self._start_fishing,
            width=12
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 停止按钮
        self.stop_button = ttk.Button(
            button_frame,
            text="停止钓鱼",
            command=self._stop_fishing,
            width=12,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 设置按钮
        self.settings_button = ttk.Button(
            button_frame,
            text="设置",
            command=self._show_settings,
            width=12
        )
        self.settings_button.pack(side=tk.LEFT)
        
        # 说明文本框架
        info_frame = ttk.LabelFrame(main_frame, text="使用说明", padding="10")
        info_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        info_text = """• 点击"开始钓鱼"启动自动钓鱼程序
• 程序会自动识别钓鱼状态并进行操作
• 可在设置中配置快捷键和显示选项
• 建议以管理员身份运行程序
• 确保模型文件和OCR程序已正确配置

状态流程：等待上钩 → 鱼上钩 → 提线中 → 钓鱼成功 → 抛竿循环"""
        
        info_label = ttk.Label(
            info_frame,
            text=info_text,
            font=("Arial", 9),
            justify=tk.LEFT,
            wraplength=450
        )
        info_label.pack(fill=tk.BOTH, expand=True)
    
    def _start_fishing(self):
        """开始钓鱼"""
        try:
            self.fishing_controller.start()
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            
            # 显示状态窗口
            if self.config.get('ui.show_status_window', True):
                self.status_window.show()
            
            logging.info("通过UI开始钓鱼")
            
        except Exception as e:
            logging.error(f"开始钓鱼失败: {e}")
            messagebox.showerror("错误", f"开始钓鱼失败: {e}")
    
    def _stop_fishing(self):
        """停止钓鱼"""
        try:
            self.fishing_controller.stop()
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            
            # 隐藏状态窗口
            self.status_window.hide()
            
            logging.info("通过UI停止钓鱼")
            
        except Exception as e:
            logging.error(f"停止钓鱼失败: {e}")
            messagebox.showerror("错误", f"停止钓鱼失败: {e}")
    
    def _show_settings(self):
        """显示设置对话框"""
        if not self.settings_dialog:
            self.settings_dialog = SettingsDialog(self.root)
        self.settings_dialog.show()
    
    def _on_state_changed(self, state: FishingState):
        """状态变化回调"""
        def update_ui():
            # 更新主界面状态
            state_text = {
                FishingState.IDLE: "空闲",
                FishingState.WAITING: "等待上钩",
                FishingState.FISH_HOOKED: "鱼已上钩",
                FishingState.PULLING_NORMAL: "正在提线",
                FishingState.PULLING_HALFWAY: "耐力不足",
                FishingState.PULL_RIGHT: "向右拉",
                FishingState.PULL_LEFT: "向左拉",
                FishingState.SUCCESS: "钓鱼成功"
            }.get(state, f"状态{state.value}")
            
            self.status_label.config(text=f"状态: {state_text}")
            
            # 更新状态窗口
            self.status_window.update_status(state)
        
        # 在主线程中更新UI
        self.root.after(0, update_ui)
    
    def _on_closing(self):
        """关闭程序"""
        try:
            # 停止钓鱼
            if self.fishing_controller.is_active():
                self.fishing_controller.stop()
            
            # 销毁状态窗口
            self.status_window.destroy()
            
            # 销毁主窗口
            self.root.destroy()
            
            logging.info("程序正常退出")
            
        except Exception as e:
            logging.error(f"程序退出时出错: {e}")
    
    def run(self):
        """运行界面"""
        try:
            # 创建状态窗口
            self.status_window.create_window(self.root)
            
            # 启动主循环
            self.root.mainloop()
            
        except Exception as e:
            logging.error(f"UI运行出错: {e}")
            raise


def main():
    """主函数"""
    # 设置日志
    logger = setup_logger('auto_fisher_ui')
    
    try:
        # 创建并运行UI
        app = FishingUI()
        app.run()
        
    except Exception as e:
        logging.error(f"程序运行出错: {e}")
        import traceback
        logging.error(traceback.format_exc())


if __name__ == '__main__':
    main() 