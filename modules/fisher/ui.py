"""
Fisher钓鱼模块UI界面
包含主控制界面、状态显示窗口和设置对话框

作者: AutoFish Team
版本: v1.0
创建时间: 2024-12-28
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
from typing import Optional, Dict, Any

from .config import fisher_config
from .fishing_controller import fishing_controller, FishingStatus, FishingState
from .model_detector import model_detector
from .hotkey_manager import hotkey_manager


class StatusWindow:
    """状态显示窗口 - 位于屏幕左上角的透明状态显示"""
    
    def __init__(self):
        """
        初始化状态显示窗口
        """
        self.window: Optional[tk.Toplevel] = None  # 状态窗口
        self.status_label: Optional[tk.Label] = None  # 状态标签
        self.is_visible = False  # 是否可见
        
    def create_window(self, parent: tk.Tk) -> None:
        """
        创建状态显示窗口
        
        Args:
            parent: 父窗口
        """
        if self.window:
            return
        
        # 创建透明顶层窗口
        self.window = tk.Toplevel(parent)
        self.window.title("钓鱼状态")
        
        # 设置窗口属性
        self.window.wm_attributes("-topmost", True)  # 置顶显示
        self.window.wm_attributes("-alpha", 0.8)     # 透明度
        self.window.resizable(False, False)          # 不可调整大小
        self.window.overrideredirect(True)           # 去除标题栏
        
        # 设置位置
        pos_x, pos_y = fisher_config.ui.status_window_position
        self.window.geometry(f"+{pos_x}+{pos_y}")
        
        # 创建状态标签
        self.status_label = tk.Label(
            self.window,
            text="状态: 停止",
            font=("微软雅黑", 12, "bold"),
            fg=fisher_config.ui.status_window_color,
            bg="white",
            padx=10,
            pady=5
        )
        self.status_label.pack()
        
        # 初始隐藏
        self.window.withdraw()
    
    def show(self) -> None:
        """显示状态窗口"""
        if self.window and not self.is_visible:
            self.window.deiconify()
            self.is_visible = True
    
    def hide(self) -> None:
        """隐藏状态窗口"""
        if self.window and self.is_visible:
            self.window.withdraw()
            self.is_visible = False
    
    def update_status(self, status: FishingStatus) -> None:
        """
        更新状态显示
        
        Args:
            status: 钓鱼状态信息
        """
        if not self.status_label:
            return
        
        # 构建状态文本
        state_text = status.current_state.value
        
        if status.current_detected_state is not None:
            state_names = fisher_config.get_state_names()
            detected_name = state_names.get(status.current_detected_state, f"状态{status.current_detected_state}")
            state_text += f"\n检测: {detected_name}"
        
        if status.round_count > 0:
            state_text += f"\n轮数: {status.round_count}"
        
        # 更新标签
        self.status_label.config(text=state_text)
    
    def destroy(self) -> None:
        """销毁窗口"""
        if self.window:
            self.window.destroy()
            self.window = None
            self.status_label = None
            self.is_visible = False


class SettingsDialog:
    """设置对话框"""
    
    def __init__(self, parent: tk.Tk):
        """
        初始化设置对话框
        
        Args:
            parent: 父窗口
        """
        self.parent = parent
        self.dialog: Optional[tk.Toplevel] = None
        
        # 设置变量
        self.show_status_var = tk.BooleanVar(value=fisher_config.ui.show_status_window)
        self.start_hotkey_var = tk.StringVar(value=fisher_config.hotkey.start_fishing)
        self.stop_hotkey_var = tk.StringVar(value=fisher_config.hotkey.stop_fishing)
        self.emergency_hotkey_var = tk.StringVar(value=fisher_config.hotkey.emergency_stop)
    
    def show(self) -> None:
        """显示设置对话框"""
        if self.dialog:
            self.dialog.lift()
            return
        
        # 创建对话框
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("钓鱼设置")
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # 创建界面
        self._create_widgets()
        
        # 居中显示
        self.dialog.geometry(f"+{self.parent.winfo_x() + 50}+{self.parent.winfo_y() + 50}")
    
    def _create_widgets(self) -> None:
        """创建设置界面组件"""
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
        
        # 热键设置组
        hotkey_group = ttk.LabelFrame(main_frame, text="热键设置", padding="10")
        hotkey_group.pack(fill=tk.X, pady=(0, 10))
        
        # 开始钓鱼热键
        start_frame = ttk.Frame(hotkey_group)
        start_frame.pack(fill=tk.X, pady=2)
        ttk.Label(start_frame, text="开始钓鱼:", width=12).pack(side=tk.LEFT)
        ttk.Entry(start_frame, textvariable=self.start_hotkey_var, width=20).pack(side=tk.LEFT, padx=(5, 0))
        
        # 停止钓鱼热键
        stop_frame = ttk.Frame(hotkey_group)
        stop_frame.pack(fill=tk.X, pady=2)
        ttk.Label(stop_frame, text="停止钓鱼:", width=12).pack(side=tk.LEFT)
        ttk.Entry(stop_frame, textvariable=self.stop_hotkey_var, width=20).pack(side=tk.LEFT, padx=(5, 0))
        
        # 紧急停止热键
        emergency_frame = ttk.Frame(hotkey_group)
        emergency_frame.pack(fill=tk.X, pady=2)
        ttk.Label(emergency_frame, text="紧急停止:", width=12).pack(side=tk.LEFT)
        ttk.Entry(emergency_frame, textvariable=self.emergency_hotkey_var, width=20).pack(side=tk.LEFT, padx=(5, 0))
        
        # 系统信息组
        info_group = ttk.LabelFrame(main_frame, text="系统信息", padding="10")
        info_group.pack(fill=tk.X, pady=(0, 10))
        
        # 模型信息
        model_info = model_detector.get_detection_info()
        model_status = "已加载" if model_info['initialized'] else "未加载"
        ttk.Label(info_group, text=f"模型状态: {model_status}").pack(anchor=tk.W)
        
        # 版本信息
        ttk.Label(info_group, text=f"版本: v1.0.9").pack(anchor=tk.W)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="保存", command=self._save_settings).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="取消", command=self._cancel).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="测试", command=self._test_settings).pack(side=tk.LEFT)
        
        # 创建版本标签
        self.version_label = tk.Label(
            button_frame, 
            text="Fisher v1.0.10",  # 更新版本号
            font=("Arial", 8),
            fg="gray"
        )
        self.version_label.pack(side=tk.BOTTOM, pady=(10, 0))
    
    def _save_settings(self) -> None:
        """保存设置"""
        try:
            # 更新配置
            fisher_config.ui.show_status_window = self.show_status_var.get()
            fisher_config.hotkey.start_fishing = self.start_hotkey_var.get()
            fisher_config.hotkey.stop_fishing = self.stop_hotkey_var.get()
            fisher_config.hotkey.emergency_stop = self.emergency_hotkey_var.get()
            
            # 保存到文件
            fisher_config.save_config()
            
            messagebox.showinfo("设置", "设置已保存")
            self._close()
            
        except Exception as e:
            messagebox.showerror("错误", f"保存设置失败: {e}")
    
    def _test_settings(self) -> None:
        """测试设置"""
        # 测试模型状态
        model_ok = model_detector.is_initialized
        
        if model_ok:
            messagebox.showinfo("测试", "系统组件工作正常")
        else:
            messagebox.showwarning("测试", "发现问题:\n模型检测器未初始化")
    
    def _cancel(self) -> None:
        """取消设置"""
        self._close()
    
    def _close(self) -> None:
        """关闭对话框"""
        if self.dialog:
            self.dialog.destroy()
            self.dialog = None


class FisherUI:
    """Fisher钓鱼模块主界面"""
    
    def __init__(self):
        """
        初始化主界面
        """
        self.root: Optional[tk.Tk] = None  # 主窗口
        self.status_window: Optional[StatusWindow] = None  # 状态窗口
        self.settings_dialog: Optional[SettingsDialog] = None  # 设置对话框
        
        # UI组件
        self.start_button: Optional[ttk.Button] = None
        self.stop_button: Optional[ttk.Button] = None
        self.settings_button: Optional[ttk.Button] = None
        self.status_text: Optional[tk.Text] = None
        
        # 状态变量
        self.is_running = False
    
    def create_window(self) -> None:
        """创建主窗口"""
        if self.root:
            return
        
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("Fisher钓鱼模块 v1.0.12")
        
        # 设置窗口大小和位置
        width, height = fisher_config.ui.main_window_size
        self.root.geometry(f"{width}x{height}")
        self.root.resizable(True, True)
        
        # 设置图标（如果有的话）
        try:
            # self.root.iconbitmap("icon.ico")
            pass
        except:
            pass
        
        # 创建界面组件
        self._create_widgets()
        
        # 创建状态窗口
        self.status_window = StatusWindow()
        self.status_window.create_window(self.root)
        
        # 设置钓鱼控制器回调
        fishing_controller.set_status_callback(self._on_status_update)
        
        # 设置热键管理器回调并启动热键监听
        hotkey_manager.set_callbacks(
            start_callback=self._hotkey_start_fishing,
            stop_callback=self._hotkey_stop_fishing,
            emergency_callback=self._hotkey_emergency_stop
        )
        if hotkey_manager.start_listening():
            self._append_status("热键监听已启动")
        else:
            self._append_status("热键监听启动失败")
        
        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _create_widgets(self) -> None:
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(
            main_frame, 
            text="Fisher智能钓鱼助手", 
            font=("微软雅黑", 16, "bold")
        )
        title_label.pack(pady=(0, 10))
        
        # 控制按钮框架
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 开始按钮
        self.start_button = ttk.Button(
            control_frame,
            text="开始钓鱼",
            command=self._start_fishing,
            style="Accent.TButton"
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # 停止按钮
        self.stop_button = ttk.Button(
            control_frame,
            text="停止钓鱼",
            command=self._stop_fishing,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # 设置按钮
        self.settings_button = ttk.Button(
            control_frame,
            text="设置",
            command=self._show_settings
        )
        self.settings_button.pack(side=tk.RIGHT)
        
        # 状态显示框架
        status_frame = ttk.LabelFrame(main_frame, text="运行状态", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        # 状态文本框
        text_frame = ttk.Frame(status_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.status_text = tk.Text(
            text_frame,
            height=10,
            wrap=tk.WORD,
            font=("Consolas", 9),
            state=tk.DISABLED
        )
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.status_text.config(yscrollcommand=scrollbar.set)
        
        # 初始状态信息
        self._append_status("Fisher钓鱼模块已启动 v1.0.12")
        self._append_status(f"模型状态: {'已加载' if model_detector.is_initialized else '未加载'}")
        self._append_status("点击'开始钓鱼'开始自动钓鱼")
    
    def _append_status(self, message: str) -> None:
        """
        添加状态信息到文本框，自动管理行数避免内存累积
        
        Args:
            message: 状态信息
        """
        if not self.status_text:
            return
        
        self.status_text.config(state=tk.NORMAL)
        
        # 检查行数，超过限制则删除旧行，防止内存无限增长
        try:
            lines = int(self.status_text.index('end-1c').split('.')[0])
            max_lines = 1000  # 最大保留行数
            
            if lines > max_lines:
                # 删除前面的行，保留最新的800行
                delete_lines = lines - 800
                self.status_text.delete('1.0', f'{delete_lines}.0')
                print(f"[UI] 清理了{delete_lines}行旧状态信息，当前行数:{lines-delete_lines}")
        except Exception as e:
            print(f"[UI] 清理文本行时出错: {e}")
        
        # 添加时间戳
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}\n"
        
        self.status_text.insert(tk.END, full_message)
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
    
    def _start_fishing(self) -> None:
        """开始钓鱼"""
        if self.is_running:
            return
        
        self._append_status("正在启动钓鱼...")
        
        # 在单独线程中启动钓鱼
        def start_thread():
            if fishing_controller.start_fishing():
                self.root.after(0, self._on_fishing_started)
            else:
                self.root.after(0, lambda: self._append_status("钓鱼启动失败"))
        
        threading.Thread(target=start_thread, daemon=True).start()
    
    def _stop_fishing(self) -> None:
        """停止钓鱼"""
        if not self.is_running:
            return
        
        self._append_status("正在停止钓鱼...")
        
        # 在单独线程中停止钓鱼
        def stop_thread():
            if fishing_controller.stop_fishing():
                self.root.after(0, self._on_fishing_stopped)
            else:
                self.root.after(0, lambda: self._append_status("钓鱼停止失败"))
        
        threading.Thread(target=stop_thread, daemon=True).start()
    
    def _hotkey_start_fishing(self) -> None:
        """热键开始钓鱼回调"""
        if self.root:
            self.root.after(0, self._start_fishing)
    
    def _hotkey_stop_fishing(self) -> None:
        """热键停止钓鱼回调"""
        if self.root:
            self.root.after(0, self._stop_fishing)
    
    def _hotkey_emergency_stop(self) -> None:
        """热键紧急停止回调"""
        if self.root:
            self.root.after(0, self._emergency_stop)
    
    def _emergency_stop(self) -> None:
        """紧急停止所有操作"""
        self._append_status("🚨 紧急停止！")
        
        # 停止钓鱼控制器
        fishing_controller.emergency_stop()
        
        # 更新UI状态
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        # 通知热键管理器状态变化
        hotkey_manager.set_fishing_active(False)
        
        # 隐藏状态窗口
        if self.status_window:
            self.status_window.hide()
    
    def _show_settings(self) -> None:
        """显示设置对话框"""
        if not self.settings_dialog:
            self.settings_dialog = SettingsDialog(self.root)
        
        self.settings_dialog.show()
    
    def _on_fishing_started(self) -> None:
        """钓鱼启动后的UI更新"""
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self._append_status("钓鱼已启动")
        
        # 通知热键管理器状态变化
        hotkey_manager.set_fishing_active(True)
        
        # 显示状态窗口
        if fisher_config.ui.show_status_window and self.status_window:
            self.status_window.show()
    
    def _on_fishing_stopped(self) -> None:
        """钓鱼停止后的UI更新"""
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self._append_status("钓鱼已停止")
        
        # 通知热键管理器状态变化
        hotkey_manager.set_fishing_active(False)
        
        # 隐藏状态窗口
        if self.status_window:
            self.status_window.hide()
    
    def _on_status_update(self, status: FishingStatus) -> None:
        """
        钓鱼状态更新回调
        
        Args:
            status: 钓鱼状态
        """
        if not self.root:
            return
        
        # 在主线程中更新UI
        def update_ui():
            # 更新状态文本
            if status.current_state == FishingState.ERROR:
                self._append_status(f"错误: {status.error_message}")
            else:
                state_msg = f"状态: {status.current_state.value}"
                if status.current_detected_state is not None:
                    state_names = fisher_config.get_state_names()
                    detected_name = state_names.get(status.current_detected_state, f"状态{status.current_detected_state}")
                    state_msg += f" | 检测: {detected_name}"
                if status.round_count > 0:
                    state_msg += f" | 轮数: {status.round_count}"
                
                self._append_status(state_msg)
            
            # 更新状态窗口
            if self.status_window:
                self.status_window.update_status(status)
            
            # 如果钓鱼停止，更新按钮状态
            if status.current_state in [FishingState.STOPPED, FishingState.ERROR]:
                self._on_fishing_stopped()
        
        self.root.after(0, update_ui)
    
    def _on_closing(self) -> None:
        """窗口关闭事件"""
        if self.is_running:
            if messagebox.askokcancel("退出", "钓鱼正在运行中，确定要退出吗？"):
                fishing_controller.emergency_stop()
                self.root.quit()
        else:
            self.root.quit()
    
    def run(self) -> None:
        """运行主界面"""
        if not self.root:
            self.create_window()
        
        # 启动主循环
        self.root.mainloop()
        
        # 清理资源
        self.cleanup()
    
    def cleanup(self) -> None:
        """清理资源"""
        print("清理UI资源")
        
        # 停止热键监听
        hotkey_manager.stop_listening()
        
        # 停止钓鱼
        if self.is_running:
            fishing_controller.emergency_stop()
        
        # 销毁状态窗口
        if self.status_window:
            self.status_window.destroy()

# 全局UI实例
fisher_ui = FisherUI() 