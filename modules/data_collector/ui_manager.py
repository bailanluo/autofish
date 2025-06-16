"""
数据采集工具UI管理器 - 负责界面创建和样式管理
将UI逻辑从主程序中分离，提高代码可维护性
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk


class UIManager:
    """UI管理器 - 负责界面创建、样式设置和UI操作"""
    
    def __init__(self, root, business_logic):
        """
        初始化UI管理器
        
        Args:
            root: Tkinter主窗口
            business_logic: 业务逻辑管理器实例
        """
        self.root = root
        self.business = business_logic
        
        # UI组件引用
        self.preview_label = None
        self.category_label = None
        self.capture_button = None
        self.pause_button = None
        self.total_stats_label = None
        self.annotation_stats_label = None
        self.status_label = None
        self.stats_canvas = None
        self.stats_scrollable_frame = None
        
        # 设置窗口和样式
        self._setup_window()
        self._setup_styles()
    
    def _setup_window(self):
        """设置主窗口属性"""
        self.root.title("🎯 YOLO数据采集工具 v2.1")
        
        # 获取屏幕真实尺寸，支持高DPI
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 根据屏幕尺寸适度调整窗口大小（减小比例）
        window_width = min(1000, int(screen_width * 0.65))
        window_height = min(700, int(screen_height * 0.65))
        min_width = min(800, int(screen_width * 0.5))
        min_height = min(600, int(screen_height * 0.5))
        
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.minsize(min_width, min_height)
        
        # 居中显示
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def _setup_styles(self):
        """设置界面样式"""
        style = ttk.Style()
        
        # 更合理的字体大小设置
        screen_width = self.root.winfo_screenwidth()
        # 降低字体缩放系数，使字体更合理
        self.base_font_size = max(9, min(12, int(screen_width / 200)))  # 基础字体：9-12
        self.large_font_size = max(10, min(14, int(screen_width / 180)))  # 大字体：10-14
        self.header_font_size = max(14, min(18, int(screen_width / 150)))  # 标题字体：14-18
        
        style.configure("Header.TLabel", font=('Microsoft YaHei', self.header_font_size, 'bold'), foreground="#2c3e50")
        style.configure("Success.TLabel", foreground="#27ae60", font=('Microsoft YaHei', self.large_font_size, 'bold'))
        style.configure("Warning.TLabel", foreground="#e74c3c", font=('Microsoft YaHei', self.large_font_size, 'bold'))
        style.configure("Status.TLabel", font=('Microsoft YaHei', self.base_font_size), foreground="#7f8c8d")
        style.configure("Highlight.TFrame", relief=tk.RAISED, background="#e8f5e8")
        style.configure("Hover.TFrame", relief=tk.RAISED, background="#f0f8ff")
        style.configure("Active.TFrame", relief=tk.SUNKEN, background="#ffeaa7")
        
        # 按钮样式
        style.configure("TButton", font=('Microsoft YaHei', self.base_font_size))
        style.configure("Large.TButton", font=('Microsoft YaHei', self.large_font_size, 'bold'))
    
    def create_main_ui(self):
        """创建主界面"""
        main_container = ttk.Frame(self.root, padding="15")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # 创建各个部分
        self._create_header(main_container)
        self._create_control_panel(main_container)
        self._create_content_area(main_container)
        self._create_status_bar(main_container)
        
        return main_container
    
    def _create_header(self, parent):
        """创建标题栏"""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(header_frame, text="🎯 全屏YOLO数据采集工具 v2.1", 
                 style="Header.TLabel").pack(side=tk.LEFT)
        
        # 设置按钮
        settings_frame = ttk.Frame(header_frame)
        settings_frame.pack(side=tk.RIGHT)
        
        ttk.Button(settings_frame, text="⚙️设置", 
                  command=self.business.open_hotkey_config,
                  style="TButton").pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(settings_frame, text="📁 数据目录", 
                  command=self.business.open_data_directory,
                  style="TButton").pack(side=tk.RIGHT)
        
        ttk.Separator(header_frame, orient='horizontal').pack(fill=tk.X, pady=10)
    
    def _create_control_panel(self, parent):
        """创建控制面板"""
        control_frame = ttk.LabelFrame(parent, text="🎮 控制面板", padding="12")
        control_frame.pack(fill=tk.X, pady=(0, 12))
        
        # 模式说明
        mode_info = ttk.Label(control_frame, 
                             text="📋 模式：全屏截图 + 目标区域标注 → 生成YOLO格式数据", 
                             font=('Microsoft YaHei', self.large_font_size), foreground="#3498db")
        mode_info.pack(fill=tk.X, pady=(0, 8))
        
        # 主要操作按钮
        select_hotkey = self.business.format_hotkey_display(
            self.business.config.get('hotkeys.select_region', 'ctrl+alt+y')
        )
        ttk.Button(control_frame, text=f"🎯 选择目标区域并设置类别 ({select_hotkey})",
                  command=self.business.select_target_region_and_category, 
                  style="Large.TButton").pack(fill=tk.X, pady=(0, 8))
        
        # 状态显示
        status_frame = ttk.Frame(control_frame)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(status_frame, text="📂 当前类别:", font=('Microsoft YaHei', self.large_font_size)).pack(side=tk.LEFT)
        self.category_label = ttk.Label(status_frame, text="未设置", style="Warning.TLabel")
        self.category_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # 快速操作按钮
        self._create_quick_actions(control_frame)
    
    def _create_quick_actions(self, parent):
        """创建快速操作按钮"""
        quick_frame = ttk.Frame(parent)
        quick_frame.pack(fill=tk.X)
        
        capture_hotkey = self.business.format_hotkey_display(
            self.business.config.get('hotkeys.quick_capture', 'y')
        )
        self.capture_button = ttk.Button(quick_frame, text=f"📸 快速采集 ({capture_hotkey})",
                                        command=self.business.quick_capture_fullscreen, 
                                        state=tk.DISABLED, style="Large.TButton")
        self.capture_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # 暂停/恢复按钮
        pause_hotkey = self.business.format_hotkey_display(
            self.business.config.get('hotkeys.pause_capture', 'ctrl+alt+p')
        )
        self.pause_button = ttk.Button(quick_frame, text=f"⏸️ 暂停 ({pause_hotkey})",
                                      command=self.business.toggle_capture_pause,
                                      style="TButton")
        self.pause_button.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(quick_frame, text="🔄 刷新", 
                  command=self.business.update_statistics,
                  style="TButton").pack(side=tk.LEFT)
    
    def _create_content_area(self, parent):
        """创建内容区域"""
        content_frame = ttk.Frame(parent)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 预览面板
        self._create_preview_panel(content_frame)
        
        # 统计面板
        self._create_statistics_panel(content_frame)
    
    def _create_preview_panel(self, parent):
        """创建预览面板"""
        preview_frame = ttk.LabelFrame(parent, text="🖼️ 全屏截图预览", padding="10")
        preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.preview_label = ttk.Label(preview_frame, 
                                      text="暂无预览图像\n\n点击选择目标区域开始YOLO数据采集\n将保存：全屏图片 + YOLO标注文件",
                                      font=('Microsoft YaHei', 12), foreground="#95a5a6",
                                      background="#ecf0f1", relief=tk.SUNKEN, anchor=tk.CENTER)
        self.preview_label.pack(expand=True, fill=tk.BOTH)
    
    def _create_statistics_panel(self, parent):
        """创建统计面板"""
        stats_frame = ttk.LabelFrame(parent, text="📊 YOLO数据统计", padding="10")
        stats_frame.pack(side=tk.RIGHT, fill=tk.BOTH)
        
        # 统计信息标题
        stats_header = ttk.Frame(stats_frame)
        stats_header.pack(fill=tk.X, pady=(0, 10))
        
        self.total_stats_label = ttk.Label(stats_header, text="总计: 0 个类别, 0 张图片", 
                                          font=('Microsoft YaHei', 11, 'bold'))
        self.total_stats_label.pack()
        
        # 标注统计信息
        self.annotation_stats_label = ttk.Label(stats_header, text="标注: 0 个标注文件", 
                                               font=('Microsoft YaHei', 10), foreground="#3498db")
        self.annotation_stats_label.pack()
        
        # 状态标签（显示热键冲突等信息）
        self.status_label = ttk.Label(stats_header, text="", 
                                     font=('Microsoft YaHei', 9), foreground="#7f8c8d")
        self.status_label.pack(pady=(5, 0))
        
        # 可滚动的类别容器
        self._create_scrollable_stats(stats_frame)
    
    def _create_scrollable_stats(self, parent):
        """创建可滚动的统计容器"""
        stats_container = ttk.Frame(parent)
        stats_container.pack(fill=tk.BOTH, expand=True)
        
        # 创建Canvas和Scrollbar
        self.stats_canvas = tk.Canvas(stats_container, width=320, height=400, bg="#fafafa")
        scrollbar = ttk.Scrollbar(stats_container, orient=tk.VERTICAL, command=self.stats_canvas.yview)
        self.stats_scrollable_frame = ttk.Frame(self.stats_canvas)
        
        # 配置滚动
        self.stats_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.stats_canvas.configure(scrollregion=self.stats_canvas.bbox("all"))
        )
        
        self.stats_canvas.create_window((0, 0), window=self.stats_scrollable_frame, anchor="nw")
        self.stats_canvas.configure(yscrollcommand=scrollbar.set)
        
        # 绑定canvas大小调整事件
        def configure_scroll_region(event):
            self.stats_canvas.configure(scrollregion=self.stats_canvas.bbox("all"))
            canvas_width = self.stats_canvas.winfo_width()
            self.stats_canvas.itemconfig(
                self.stats_canvas.find_all()[0], 
                width=canvas_width
            )
        
        self.stats_canvas.bind('<Configure>', configure_scroll_region)
        
        # 布局
        self.stats_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 鼠标滚轮支持
        self._bind_mousewheel()
    
    def _create_status_bar(self, parent):
        """创建状态栏"""
        status_panel = ttk.Frame(parent)
        status_panel.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Separator(status_panel, orient='horizontal').pack(fill=tk.X, pady=(0, 10))
        
        status_info = ttk.Frame(status_panel)
        status_info.pack(fill=tk.X)
        
        ttk.Label(status_info, text="🟢 就绪", style="Status.TLabel").pack(side=tk.LEFT)
        ttk.Label(status_info, text="数据保存路径: data/images/", style="Status.TLabel").pack(side=tk.RIGHT)
    
    def _bind_mousewheel(self):
        """绑定鼠标滚轮事件（递归绑定所有子控件）"""
        def _on_mousewheel(event):
            self.stats_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def bind_recursive(widget):
            """递归绑定所有子控件的鼠标滚轮事件"""
            widget.bind("<MouseWheel>", _on_mousewheel)
            for child in widget.winfo_children():
                bind_recursive(child)
        
        # 绑定到canvas和scrollable_frame
        self.stats_canvas.bind("<MouseWheel>", _on_mousewheel)
        bind_recursive(self.stats_scrollable_frame)
        
        # 定期更新绑定（当添加新的类别标签时）
        def update_bindings():
            bind_recursive(self.stats_scrollable_frame)
            self.root.after(1000, update_bindings)
        
        self.root.after(100, update_bindings)
    
    def update_preview(self, image: Image.Image):
        """更新预览图像"""
        try:
            # 获取预览区域的实际尺寸
            self.preview_label.update_idletasks()
            label_width = self.preview_label.winfo_width()
            label_height = self.preview_label.winfo_height()
            
            # 如果标签尺寸还未初始化，使用默认值
            if label_width <= 1 or label_height <= 1:
                label_width = 400
                label_height = 300
            
            # 计算缩放比例，保持宽高比
            image_width, image_height = image.size
            width_ratio = label_width / image_width
            height_ratio = label_height / image_height
            scale_ratio = min(width_ratio, height_ratio) * 0.95
            
            # 计算新尺寸
            new_width = int(image_width * scale_ratio)
            new_height = int(image_height * scale_ratio)
            
            # 确保最小尺寸
            new_width = max(new_width, 100)
            new_height = max(new_height, 100)
            
            # 缩放图像
            image_copy = image.copy()
            image_copy = image_copy.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 转换为PhotoImage并显示
            photo = ImageTk.PhotoImage(image_copy)
            self.preview_label.config(image=photo, text="", compound=tk.CENTER)
            self.preview_label.image = photo  # 保持引用防止被垃圾回收
            
        except Exception as e:
            # 显示错误信息
            self.preview_label.config(image="", text=f"预览失败\n{str(e)}", 
                                     font=('Microsoft YaHei', 11), foreground="#e74c3c")
    
    def update_button_text_by_partial_match(self, partial_text: str, new_text: str):
        """根据部分文本匹配更新按钮文本"""
        def update_recursive(widget):
            if hasattr(widget, 'config') and hasattr(widget, 'cget'):
                try:
                    current_text = widget.cget('text')
                    if isinstance(current_text, str) and partial_text in current_text:
                        widget.config(text=new_text)
                        return True
                except:
                    pass
            
            # 递归检查子控件
            try:
                for child in widget.winfo_children():
                    if update_recursive(child):
                        return True
            except:
                pass
            return False
        
        update_recursive(self.root) 