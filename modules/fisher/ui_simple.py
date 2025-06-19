"""
Fisher钓鱼模块UI界面 - 简单美化版本
在现有功能基础上进行界面美化，不添加新功能

作者: AutoFish Team
版本: v1.0.14
创建时间: 2025-01-17
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
from typing import Optional, Dict, Any

from .config import fisher_config
from .fishing_controller import fishing_controller, FishingStatus, FishingState
from .model_detector import model_detector
from .hotkey_manager import hotkey_manager


# 美化主题配置
class UIStyle:
    """UI样式配置"""
    
    # 颜色方案
    COLORS = {
        'bg_primary': '#2C3E50',      # 主背景色
        'bg_secondary': '#34495E',    # 次要背景色
        'accent': '#3498DB',          # 强调色 - 蓝色
        'success': '#27AE60',         # 成功色 - 绿色
        'warning': '#E74C3C',         # 警告色 - 红色
        'text_light': '#ECF0F1',      # 浅色文字
        'text_dark': '#2C3E50',       # 深色文字
        'border': '#BDC3C7',          # 边框色
    }
    
    # 字体配置
    FONTS = {
        'title': ('微软雅黑', 16, 'bold'),
        'button': ('微软雅黑', 11, 'bold'),
        'text': ('微软雅黑', 10),
        'console': ('Consolas', 9),
    }


class StatusWindow:
    """状态显示窗口 - 美化版本"""
    
    def __init__(self):
        self.window: Optional[tk.Toplevel] = None
        self.status_label: Optional[tk.Label] = None
        self.is_visible = False
        
    def create_window(self, parent: tk.Tk) -> None:
        if self.window:
            return
        
        self.window = tk.Toplevel(parent)
        self.window.title("钓鱼状态")
        
        # 窗口样式
        self.window.wm_attributes("-topmost", True)
        self.window.wm_attributes("-alpha", 0.9)  # 提高透明度
        self.window.resizable(False, False)
        self.window.overrideredirect(True)
        
        # 设置圆角效果（通过边框实现）
        self.window.configure(bg=UIStyle.COLORS['bg_primary'])
        
        # 位置
        pos_x, pos_y = fisher_config.ui.status_window_position
        self.window.geometry(f"+{pos_x}+{pos_y}")
        
        # 主容器
        main_frame = tk.Frame(
            self.window,
            bg=UIStyle.COLORS['bg_primary'],
            relief='raised',
            borderwidth=2
        )
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 状态标签
        self.status_label = tk.Label(
            main_frame,
            text="状态: 停止",
            font=UIStyle.FONTS['text'],
            fg=UIStyle.COLORS['text_light'],
            bg=UIStyle.COLORS['bg_primary'],
            padx=15,
            pady=10
        )
        self.status_label.pack()
        
        self.window.withdraw()
    
    def show(self) -> None:
        if self.window and not self.is_visible:
            self.window.deiconify()
            self.is_visible = True
    
    def hide(self) -> None:
        if self.window and self.is_visible:
            self.window.withdraw()
            self.is_visible = False
    
    def update_status(self, status: FishingStatus) -> None:
        if not self.status_label:
            return
        
        state_text = status.current_state.value
        
        if status.current_detected_state is not None:
            state_names = fisher_config.get_state_names()
            detected_name = state_names.get(status.current_detected_state, f"状态{status.current_detected_state}")
            state_text += f"\n检测: {detected_name}"
        
        if status.round_count > 0:
            state_text += f"\n轮数: {status.round_count}"
        
        self.status_label.config(text=state_text)
    
    def destroy(self) -> None:
        if self.window:
            self.window.destroy()
            self.window = None
            self.status_label = None
            self.is_visible = False


class SettingsDialog:
    """设置对话框 - 美化版本"""
    
    def __init__(self, parent: tk.Tk):
        self.parent = parent
        self.dialog: Optional[tk.Toplevel] = None
        
        # 设置变量
        self.show_status_var = tk.BooleanVar(value=fisher_config.ui.show_status_window)
        self.start_hotkey_var = tk.StringVar(value=fisher_config.hotkey.start_fishing)
        self.stop_hotkey_var = tk.StringVar(value=fisher_config.hotkey.stop_fishing)
        self.emergency_hotkey_var = tk.StringVar(value=fisher_config.hotkey.emergency_stop)
    
    def show(self) -> None:
        if self.dialog:
            self.dialog.lift()
            return
        
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("钓鱼设置")
        self.dialog.geometry("450x350")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.dialog.configure(bg=UIStyle.COLORS['bg_secondary'])
        
        self._create_widgets()
        
        # 居中显示
        self.dialog.geometry(f"+{self.parent.winfo_x() + 50}+{self.parent.winfo_y() + 50}")
    
    def _create_widgets(self) -> None:
        # 主框架
        main_frame = tk.Frame(
            self.dialog,
            bg=UIStyle.COLORS['bg_secondary'],
            padx=20,
            pady=20
        )
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = tk.Label(
            main_frame,
            text="⚙ 钓鱼设置",
            font=UIStyle.FONTS['title'],
            fg=UIStyle.COLORS['text_light'],
            bg=UIStyle.COLORS['bg_secondary']
        )
        title_label.pack(pady=(0, 20))
        
        # 界面设置组
        ui_frame = tk.LabelFrame(
            main_frame,
            text="界面设置",
            font=UIStyle.FONTS['text'],
            fg=UIStyle.COLORS['text_light'],
            bg=UIStyle.COLORS['bg_secondary'],
            borderwidth=2,
            relief='groove'
        )
        ui_frame.pack(fill=tk.X, pady=(0, 15))
        
        ui_content = tk.Frame(ui_frame, bg=UIStyle.COLORS['bg_secondary'])
        ui_content.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Checkbutton(
            ui_content,
            text="显示状态窗口",
            variable=self.show_status_var,
            font=UIStyle.FONTS['text'],
            fg=UIStyle.COLORS['text_light'],
            bg=UIStyle.COLORS['bg_secondary'],
            selectcolor=UIStyle.COLORS['accent'],
            activebackground=UIStyle.COLORS['bg_secondary'],
            activeforeground=UIStyle.COLORS['text_light']
        ).pack(anchor=tk.W)
        
        # 热键设置组
        hotkey_frame = tk.LabelFrame(
            main_frame,
            text="热键设置",
            font=UIStyle.FONTS['text'],
            fg=UIStyle.COLORS['text_light'],
            bg=UIStyle.COLORS['bg_secondary'],
            borderwidth=2,
            relief='groove'
        )
        hotkey_frame.pack(fill=tk.X, pady=(0, 15))
        
        hotkey_content = tk.Frame(hotkey_frame, bg=UIStyle.COLORS['bg_secondary'])
        hotkey_content.pack(fill=tk.X, padx=15, pady=10)
        
        # 热键设置项
        hotkey_items = [
            ("开始钓鱼:", self.start_hotkey_var),
            ("停止钓鱼:", self.stop_hotkey_var),
            ("紧急停止:", self.emergency_hotkey_var)
        ]
        
        for i, (label_text, var) in enumerate(hotkey_items):
            item_frame = tk.Frame(hotkey_content, bg=UIStyle.COLORS['bg_secondary'])
            item_frame.pack(fill=tk.X, pady=3)
            
            tk.Label(
                item_frame,
                text=label_text,
                font=UIStyle.FONTS['text'],
                fg=UIStyle.COLORS['text_light'],
                bg=UIStyle.COLORS['bg_secondary'],
                width=12,
                anchor=tk.W
            ).pack(side=tk.LEFT)
            
            tk.Entry(
                item_frame,
                textvariable=var,
                font=UIStyle.FONTS['text'],
                width=15,
                relief='flat',
                borderwidth=2
            ).pack(side=tk.LEFT, padx=(10, 0))
        
        # 系统信息组
        info_frame = tk.LabelFrame(
            main_frame,
            text="系统信息",
            font=UIStyle.FONTS['text'],
            fg=UIStyle.COLORS['text_light'],
            bg=UIStyle.COLORS['bg_secondary'],
            borderwidth=2,
            relief='groove'
        )
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        info_content = tk.Frame(info_frame, bg=UIStyle.COLORS['bg_secondary'])
        info_content.pack(fill=tk.X, padx=15, pady=10)
        
        # 模型状态
        model_info = model_detector.get_detection_info()
        model_status = "✅ 已加载" if model_info['initialized'] else "❌ 未加载"
        
        tk.Label(
            info_content,
            text=f"模型状态: {model_status}",
            font=UIStyle.FONTS['text'],
            fg=UIStyle.COLORS['text_light'],
            bg=UIStyle.COLORS['bg_secondary']
        ).pack(anchor=tk.W)
        
        # 按钮区域
        button_frame = tk.Frame(main_frame, bg=UIStyle.COLORS['bg_secondary'])
        button_frame.pack(fill=tk.X)
        
        # 按钮样式
        button_style = {
            'font': UIStyle.FONTS['button'],
            'relief': 'flat',
            'borderwidth': 0,
            'cursor': 'hand2',
            'width': 8,
            'pady': 8
        }
        
        # 保存按钮
        save_btn = tk.Button(
            button_frame,
            text="保存",
            bg=UIStyle.COLORS['success'],
            fg=UIStyle.COLORS['text_light'],
            command=self._save_settings,
            **button_style
        )
        save_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 取消按钮
        cancel_btn = tk.Button(
            button_frame,
            text="取消",
            bg=UIStyle.COLORS['warning'],
            fg=UIStyle.COLORS['text_light'],
            command=self._cancel,
            **button_style
        )
        cancel_btn.pack(side=tk.RIGHT)
        
        # 为按钮添加悬停效果
        self._add_hover_effect(save_btn, UIStyle.COLORS['success'])
        self._add_hover_effect(cancel_btn, UIStyle.COLORS['warning'])
        
        self.dialog.protocol("WM_DELETE_WINDOW", self._close)
    
    def _add_hover_effect(self, button, normal_color):
        """添加按钮悬停效果"""
        def on_enter(e):
            # 变暗效果
            darker_color = self._darken_color(normal_color)
            button.configure(bg=darker_color)
        
        def on_leave(e):
            button.configure(bg=normal_color)
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
    
    def _darken_color(self, color):
        """颜色变暗效果"""
        color_map = {
            UIStyle.COLORS['success']: '#219A52',
            UIStyle.COLORS['warning']: '#C0392B',
            UIStyle.COLORS['accent']: '#2E86C1',
            UIStyle.COLORS['bg_secondary']: '#2C3E50',  # 置顶按钮的变暗色
            UIStyle.COLORS['bg_primary']: '#1A252F',    # 主背景的变暗色
            '#FFFFFF': '#F8F9FA'  # 白色的变暗色
        }
        return color_map.get(color, color)
    
    def _save_settings(self) -> None:
        # 保存设置逻辑（与原版相同）
        fisher_config.ui.show_status_window = self.show_status_var.get()
        fisher_config.hotkey.start_fishing = self.start_hotkey_var.get()
        fisher_config.hotkey.stop_fishing = self.stop_hotkey_var.get()
        fisher_config.hotkey.emergency_stop = self.emergency_hotkey_var.get()
        
        # 保存到配置文件
        fisher_config.save_config()
        
        # 重新设置热键
        hotkey_manager.update_hotkeys()
        
        messagebox.showinfo("成功", "设置已保存！")
        self._close()
    
    def _cancel(self) -> None:
        self._close()
    
    def _close(self) -> None:
        if self.dialog:
            self.dialog.destroy()
            self.dialog = None


class FisherUI:
    """Fisher钓鱼模块UI界面 - 美化版本"""
    
    def __init__(self):
        self.root: Optional[tk.Tk] = None
        self.status_text: Optional[tk.Text] = None
        self.start_button: Optional[tk.Button] = None
        self.stop_button: Optional[tk.Button] = None
        self.settings_button: Optional[tk.Button] = None
        self.pin_button: Optional[tk.Button] = None  # 置顶按钮
        
        # 状态管理
        self.is_running = False
        self.is_always_on_top = False  # 置顶状态
        self.status_window = StatusWindow()
        self.settings_dialog: Optional[SettingsDialog] = None
    
    def create_window(self) -> None:
        """创建主窗口"""
        self.root = tk.Tk()
        self.root.title("🎣 Fisher智能钓鱼助手 v1.0.14")
        self.root.geometry("600x500")
        self.root.configure(bg=UIStyle.COLORS['bg_primary'])
        
        # 设置窗口图标（如果有的话）
        try:
            self.root.iconbitmap("assets/icons/fisher.ico")
        except:
            pass
        
        # 居中窗口
        self._center_window()
        
        # 设置最小尺寸
        self.root.minsize(500, 400)
        
        # 创建界面组件
        self._create_widgets()
        
        # 创建状态窗口
        self.status_window.create_window(self.root)
        
        # 设置钓鱼控制器状态更新回调
        fishing_controller.set_status_callback(self._on_status_update)
        
        # 启动热键监听
        try:
            hotkey_manager.set_callbacks(
                start_callback=self._hotkey_start_fishing,
                stop_callback=self._hotkey_stop_fishing,
                emergency_callback=self._emergency_stop
            )
            hotkey_manager.start_listening()
            self._append_status("✅ 热键监听已启动")
        except Exception as e:
            self._append_status(f"❌ 热键监听启动失败: {e}")
        
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _center_window(self):
        """窗口居中"""
        self.root.update_idletasks()
        width = 600
        height = 500
        x = (self.root.winfo_screenwidth() - width) // 2
        y = (self.root.winfo_screenheight() - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def _create_widgets(self) -> None:
        """创建界面组件"""
        # 主容器
        main_container = tk.Frame(
            self.root,
            bg=UIStyle.COLORS['bg_primary'],
            padx=20,
            pady=20
        )
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # 标题区域
        title_frame = tk.Frame(main_container, bg=UIStyle.COLORS['bg_primary'])
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 置顶按钮（左上角）- 重新设计版本
        pin_container = tk.Frame(title_frame, bg=UIStyle.COLORS['bg_primary'])
        pin_container.pack(side=tk.LEFT, anchor='nw', padx=(0, 15), pady=(5, 0))
        
        self.pin_button = tk.Button(
            pin_container,
            text="📌",  # 使用标准的曲别针图标
            font=('Segoe UI Emoji', 18),  # 更大字体确保居中
            bg=UIStyle.COLORS['bg_primary'],  # 默认与背景同色
            fg=UIStyle.COLORS['text_light'],  # 白色图标
            activebackground=UIStyle.COLORS['bg_secondary'],  # 按下时稍微变亮
            activeforeground=UIStyle.COLORS['text_light'],
            command=self._toggle_pin,
            relief='flat',
            borderwidth=0,
            cursor='hand2',
            width=2,  # 减小宽度让图标更居中
            height=1,
            highlightthickness=0,
            padx=0,  # 移除内边距
            pady=0   # 移除内边距
        )
        self.pin_button.pack()
        
        # 标题容器（居中）
        title_container = tk.Frame(title_frame, bg=UIStyle.COLORS['bg_primary'])
        title_container.pack(expand=True)
        
        # 主标题
        title_label = tk.Label(
            title_container,
            text="🎣 Fisher智能钓鱼助手",
            font=UIStyle.FONTS['title'],
            fg=UIStyle.COLORS['text_light'],
            bg=UIStyle.COLORS['bg_primary']
        )
        title_label.pack()
        
        # 版本信息
        version_label = tk.Label(
            title_container,
            text="v1.0.14 - 基于YOLO深度学习",
            font=('微软雅黑', 9),
            fg=UIStyle.COLORS['border'],
            bg=UIStyle.COLORS['bg_primary']
        )
        version_label.pack(pady=(5, 0))
        
        # 控制按钮区域
        control_frame = tk.Frame(main_container, bg=UIStyle.COLORS['bg_primary'])
        control_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 按钮样式
        button_style = {
            'font': UIStyle.FONTS['button'],
            'relief': 'flat',
            'borderwidth': 0,
            'cursor': 'hand2',
            'height': 2,
            'width': 12
        }
        
        # 开始按钮
        self.start_button = tk.Button(
            control_frame,
            text="🚀 开始钓鱼",
            bg=UIStyle.COLORS['success'],
            fg=UIStyle.COLORS['text_light'],
            command=self._start_fishing,
            **button_style
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 停止按钮
        self.stop_button = tk.Button(
            control_frame,
            text="⏹ 停止钓鱼",
            bg=UIStyle.COLORS['warning'],
            fg=UIStyle.COLORS['text_light'],
            command=self._stop_fishing,
            state=tk.DISABLED,
            **button_style
        )
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 设置按钮
        self.settings_button = tk.Button(
            control_frame,
            text="⚙ 设置",
            bg=UIStyle.COLORS['accent'],
            fg=UIStyle.COLORS['text_light'],
            command=self._show_settings,
            **button_style
        )
        self.settings_button.pack(side=tk.RIGHT)
        
        # 为按钮添加悬停效果
        self._add_hover_effect(self.start_button, UIStyle.COLORS['success'])
        self._add_hover_effect(self.stop_button, UIStyle.COLORS['warning'])
        self._add_hover_effect(self.settings_button, UIStyle.COLORS['accent'])
        
        # 为置顶按钮添加特殊悬停效果
        self._add_pin_hover_effect()
        
        # 状态显示区域
        status_frame = tk.LabelFrame(
            main_container,
            text="📊 运行状态",
            font=UIStyle.FONTS['text'],
            fg=UIStyle.COLORS['text_light'],
            bg=UIStyle.COLORS['bg_primary'],
            borderwidth=2,
            relief='groove'
        )
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        # 状态文本区域
        text_container = tk.Frame(status_frame, bg=UIStyle.COLORS['bg_primary'])
        text_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 状态文本框
        self.status_text = tk.Text(
            text_container,
            font=UIStyle.FONTS['console'],
            bg=UIStyle.COLORS['bg_secondary'],
            fg=UIStyle.COLORS['text_light'],
            insertbackground=UIStyle.COLORS['text_light'],
            selectbackground=UIStyle.COLORS['accent'],
            selectforeground=UIStyle.COLORS['text_light'],
            relief='flat',
            borderwidth=2,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = tk.Scrollbar(
            text_container,
            orient=tk.VERTICAL,
            command=self.status_text.yview,
            bg=UIStyle.COLORS['bg_secondary'],
            troughcolor=UIStyle.COLORS['bg_primary'],
            activebackground=UIStyle.COLORS['accent']
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.status_text.config(yscrollcommand=scrollbar.set)
        
        # 初始状态信息
        self._append_status("🎉 Fisher钓鱼模块已启动 v1.0.14")
        model_status = "✅ 已加载" if model_detector.is_initialized else "❌ 未加载"
        self._append_status(f"🤖 模型状态: {model_status}")
        self._append_status("💡 点击'开始钓鱼'开始自动钓鱼")
        self._append_status(f"⌨️ 热键: {fisher_config.hotkey.start_fishing}=开始/停止, {fisher_config.hotkey.emergency_stop}=紧急停止")
        self._append_status("📌 提示: 点击左上角📌按钮可设置窗口置顶，在游戏中也能看到日志")
    
    def _add_hover_effect(self, button, normal_color):
        """添加按钮悬停效果"""
        def on_enter(e):
            if button['state'] != 'disabled':
                darker_color = self._darken_color(normal_color)
                button.configure(bg=darker_color)
        
        def on_leave(e):
            if button['state'] != 'disabled':
                button.configure(bg=normal_color)
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
    
    def _darken_color(self, color):
        """颜色变暗效果"""
        color_map = {
            UIStyle.COLORS['success']: '#219A52',
            UIStyle.COLORS['warning']: '#C0392B',
            UIStyle.COLORS['accent']: '#2E86C1',
            UIStyle.COLORS['bg_secondary']: '#2C3E50',  # 置顶按钮的变暗色
            UIStyle.COLORS['bg_primary']: '#1A252F',    # 主背景的变暗色
            '#FFFFFF': '#F8F9FA'  # 白色的变暗色
        }
        return color_map.get(color, color)
    
    def _append_status(self, message: str) -> None:
        """添加状态信息"""
        if not self.status_text:
            return
        
        self.status_text.config(state=tk.NORMAL)
        
        # 管理行数，避免内存累积
        try:
            lines = int(self.status_text.index('end-1c').split('.')[0])
            max_lines = 1000
            
            if lines > max_lines:
                delete_lines = lines - 800
                self.status_text.delete('1.0', f'{delete_lines}.0')
        except:
            pass
        
        # 添加时间戳和消息
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}\n"
        
        self.status_text.insert(tk.END, full_message)
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
    
    # 以下方法与原版UI功能相同，只是保持了美化的样式
    def _start_fishing(self) -> None:
        if self.is_running:
            return
        
        self._append_status("🚀 正在启动钓鱼...")
        
        def start_thread():
            if fishing_controller.start_fishing():
                self.root.after(0, self._on_fishing_started)
            else:
                self.root.after(0, lambda: self._append_status("❌ 钓鱼启动失败"))
        
        threading.Thread(target=start_thread, daemon=True).start()
    
    def _stop_fishing(self) -> None:
        if not self.is_running:
            return
        
        self._append_status("⏹ 正在停止钓鱼...")
        
        def stop_thread():
            if fishing_controller.stop_fishing():
                self.root.after(0, self._on_fishing_stopped)
            else:
                self.root.after(0, lambda: self._append_status("❌ 钓鱼停止失败"))
        
        threading.Thread(target=stop_thread, daemon=True).start()
    
    def _hotkey_start_fishing(self) -> None:
        if self.root:
            self.root.after(0, self._start_fishing)
    
    def _hotkey_stop_fishing(self) -> None:
        if self.root:
            self.root.after(0, self._stop_fishing)
    
    def _emergency_stop(self) -> None:
        self._append_status("🚨 紧急停止！")
        fishing_controller.emergency_stop()
        
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        hotkey_manager.set_fishing_active(False)
        
        if self.status_window:
            self.status_window.hide()
    
    def _show_settings(self) -> None:
        if not self.settings_dialog:
            self.settings_dialog = SettingsDialog(self.root)
        
        self.settings_dialog.show()
    
    def _on_fishing_started(self) -> None:
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self._append_status("✅ 钓鱼已启动")
        
        hotkey_manager.set_fishing_active(True)
        
        if fisher_config.ui.show_status_window and self.status_window:
            self.status_window.show()
    
    def _on_fishing_stopped(self) -> None:
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self._append_status("⏹ 钓鱼已停止")
        
        hotkey_manager.set_fishing_active(False)
        
        if self.status_window:
            self.status_window.hide()
    
    def _on_status_update(self, status: FishingStatus) -> None:
        def update_ui():
            if self.status_window:
                self.status_window.update_status(status)
            
            # 在主界面显示状态变化
            state_names = fisher_config.get_state_names()
            current_state_name = status.current_state.value
            
            if status.current_detected_state is not None:
                detected_name = state_names.get(status.current_detected_state, f"状态{status.current_detected_state}")
                self._append_status(f"🎯 {current_state_name} | 检测: {detected_name}")
            
            if status.round_count > 0:
                self._append_status(f"🏆 完成第 {status.round_count} 轮钓鱼")
        
        if self.root:
            self.root.after(0, update_ui)
    
    def _on_closing(self) -> None:
        if self.is_running:
            if messagebox.askokcancel("退出", "钓鱼正在运行中，确定要退出吗？"):
                fishing_controller.stop_fishing()
                self.cleanup()
                self.root.destroy()
        else:
            self.cleanup()
            self.root.destroy()
    
    def run(self) -> None:
        if not self.root:
            self.create_window()
        
        self.root.mainloop()
    
    def cleanup(self) -> None:
        try:
            if hasattr(fishing_controller, 'cleanup'):
                fishing_controller.cleanup()
            
            if hasattr(hotkey_manager, 'cleanup'):
                hotkey_manager.cleanup()
            
            if self.status_window:
                self.status_window.destroy()
                
        except Exception as e:
            print(f"清理资源时出错: {e}")

    def _toggle_pin(self) -> None:
        """切换窗口置顶状态"""
        self.is_always_on_top = not self.is_always_on_top
        
        if self.root:
            if self.is_always_on_top:
                # 设置窗口置顶
                self.root.attributes('-topmost', True)
                # 置顶状态：白色背景+黑色图标（颜色反转）
                self.pin_button.configure(
                    bg='#FFFFFF',  # 白色背景
                    fg='#2C3E50',  # 深色图标
                    text="📌",
                    activebackground='#F8F9FA',  # 按下时稍微变暗的白色
                    activeforeground='#2C3E50'
                )
                self._append_status("📌 窗口已设置为置顶，在游戏中也可以看到界面")
            else:
                # 取消窗口置顶
                self.root.attributes('-topmost', False)
                # 默认状态：与背景同色
                self.pin_button.configure(
                    bg=UIStyle.COLORS['bg_primary'],  # 与背景同色
                    fg=UIStyle.COLORS['text_light'],  # 白色图标
                    text="📌",
                    activebackground=UIStyle.COLORS['bg_secondary'],
                    activeforeground=UIStyle.COLORS['text_light']
                )
                self._append_status("📌 窗口置顶已取消")
    
    def _add_pin_hover_effect(self):
        """为置顶按钮添加特殊悬停效果"""
        def on_enter(e):
            # 根据当前状态选择悬停颜色
            if self.is_always_on_top:
                # 置顶状态：白色稍微变暗
                hover_color = '#F8F9FA'
            else:
                # 默认状态：背景色稍微变亮
                hover_color = UIStyle.COLORS['bg_secondary']
            self.pin_button.configure(bg=hover_color)
        
        def on_leave(e):
            # 根据当前状态恢复颜色
            if self.is_always_on_top:
                self.pin_button.configure(bg='#FFFFFF')  # 白色背景
            else:
                self.pin_button.configure(bg=UIStyle.COLORS['bg_primary'])  # 背景色
        
        self.pin_button.bind("<Enter>", on_enter)
        self.pin_button.bind("<Leave>", on_leave)
        
        # 右键显示帮助
        def show_pin_help(e):
            status = "已激活" if self.is_always_on_top else "未激活"
            self._append_status(f"💡 置顶功能当前{status} - 右键查看此帮助")
            
        self.pin_button.bind("<Button-3>", show_pin_help)


# 全局UI实例
fisher_ui = FisherUI() 