"""
数据采集工具业务逻辑管理器 - 负责核心功能实现
将业务逻辑从主程序中分离，提高代码可维护性
"""

import os
import sys
import ctypes
import platform
import subprocess
from tkinter import messagebox, simpledialog
from PIL import Image, ImageDraw, ImageFont
from typing import Dict

# 添加主项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from modules.logger import setup_logger

# 导入模块 - 支持直接运行和模块导入
try:
    from .config_manager import DataCollectorConfig
    from .screen_capture import ScreenCapture
    from .data_manager import DataManager
    from .hotkey_listener import HotkeyListener
    from .hotkey_config_dialog import HotkeyDetectionDialog
    from .system_settings_dialog import SystemSettingsDialog
except ImportError:
    from config_manager import DataCollectorConfig
    from screen_capture import ScreenCapture
    from data_manager import DataManager
    from hotkey_listener import HotkeyListener
    from hotkey_config_dialog import HotkeyDetectionDialog
    from system_settings_dialog import SystemSettingsDialog


class BusinessLogic:
    """业务逻辑管理器 - 负责数据采集、配置管理等核心功能"""
    
    def __init__(self, root):
        """
        初始化业务逻辑管理器
        
        Args:
            root: Tkinter主窗口
        """
        self.root = root
        self.logger = setup_logger('DataCollectorApp')
        
        # 检查管理员权限
        self.is_admin = self._check_admin_privileges()
        if not self.is_admin:
            self.logger.warning("程序未以管理员身份运行，某些热键功能可能受限")
        
        # 初始化组件
        self.config = DataCollectorConfig()
        self.data_manager = DataManager()
        self.screen_capture = ScreenCapture()
        self.hotkey_listener = None
        self.hotkey_listening_failed = False
        
        # 应用状态
        self.current_target_region = None
        self.current_category = None
        self.capture_paused = False
        
        # UI管理器引用（后续设置）
        self.ui_manager = None
        
        # 设置热键监听
        self._setup_hotkeys()
        
        self.logger.info("业务逻辑管理器初始化完成")
    
    def set_ui_manager(self, ui_manager):
        """设置UI管理器引用"""
        self.ui_manager = ui_manager
    
    def _check_admin_privileges(self) -> bool:
        """检查是否以管理员身份运行"""
        try:
            if platform.system() == 'Windows':
                return ctypes.windll.shell32.IsUserAnAdmin()
            else:
                return os.geteuid() == 0
        except:
            return False
    
    def format_hotkey_display(self, hotkey: str) -> str:
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
            else:
                display_parts.append(part.upper())
        
        return '+'.join(display_parts)
    
    def _setup_hotkeys(self):
        """设置热键监听"""
        try:
            hotkey_config = self.config.get_hotkeys()
            callbacks = {
                'select_region': self.select_target_region_and_category,
                'quick_capture': self.quick_capture_fullscreen,
                'pause_capture': self.toggle_capture_pause
            }
            
            self.hotkey_listener = HotkeyListener(hotkey_config, callbacks)
            self.hotkey_listener.start_listening()
            
            # 检查热键监听是否成功
            if not self.hotkey_listener.is_listening:
                self.hotkey_listening_failed = True
                self.logger.warning("热键监听启动失败")
            
        except Exception as e:
            self.hotkey_listening_failed = True
            self.logger.error(f"热键监听设置失败: {e}")
    
    def open_hotkey_config(self):
        """打开热键配置对话框"""
        try:
            # 暂停热键监听
            if self.hotkey_listener:
                self.hotkey_listener.pause_listening()
            
            current_hotkeys = self.config.get_hotkeys()
            
            # 创建对话框并传递自动保存回调
            dialog = HotkeyDetectionDialog(self.root, current_hotkeys, self._apply_hotkey_config)
            
            if dialog.result:
                # 保存新的热键配置
                self.config.set_hotkeys(dialog.result)
                self.config.save_config()
                
                # 更新热键监听器
                if self.hotkey_listener:
                    self.hotkey_listener.update_hotkeys(dialog.result)
                
                # 更新界面上的热键显示
                self._update_hotkey_displays()
                
                # 检查热键冲突并显示警告
                self._check_and_display_hotkey_conflicts()
                
                # 移除弹窗提示，因为已经有自动保存提示了
                self.logger.info("热键配置已更新完成")
                
        except Exception as e:
            self.logger.error(f"热键配置失败: {e}")
            messagebox.showerror("错误", f"热键配置失败: {e}")
        finally:
            # 恢复热键监听
            if self.hotkey_listener:
                self.hotkey_listener.resume_listening()
    
    def _apply_hotkey_config(self, new_hotkeys: Dict[str, str]):
        """应用热键配置（自动保存时调用）"""
        try:
            # 保存到配置文件
            self.config.set_hotkeys(new_hotkeys)
            self.config.save_config()
            
            # 更新热键监听器
            if self.hotkey_listener:
                self.hotkey_listener.update_hotkeys(new_hotkeys)
            
            # 更新界面显示
            self._update_hotkey_displays()
            
            # 检查冲突
            self._check_and_display_hotkey_conflicts()
            
            self.logger.info(f"热键配置已自动更新: {new_hotkeys}")
            
        except Exception as e:
            self.logger.error(f"自动更新热键配置失败: {e}")
    
    def _update_hotkey_displays(self):
        """更新界面上的热键显示"""
        try:
            current_hotkeys = self.config.get_hotkeys()
            
            # 更新选择区域按钮
            select_hotkey = self.format_hotkey_display(current_hotkeys.get('select_region', 'ctrl+alt+y'))
            select_button_text = f"🎯 选择目标区域并设置类别 ({select_hotkey})"
            
            # 查找并更新选择区域按钮
            if self.ui_manager:
                self.ui_manager.update_button_text_by_partial_match("选择目标区域", select_button_text)
            
            # 更新快速采集按钮
            capture_hotkey = self.format_hotkey_display(current_hotkeys.get('quick_capture', 'y'))
            capture_button_text = f"📸 快速采集 ({capture_hotkey})"
            
            if self.ui_manager and hasattr(self.ui_manager, 'capture_button'):
                self.ui_manager.capture_button.config(text=capture_button_text)
            
            # 更新暂停按钮
            pause_hotkey = self.format_hotkey_display(current_hotkeys.get('pause_capture', 'ctrl+alt+p'))
            if self.capture_paused:
                pause_button_text = f"▶️ 恢复 ({pause_hotkey})"
            else:
                pause_button_text = f"⏸️ 暂停 ({pause_hotkey})"
                
            if self.ui_manager and hasattr(self.ui_manager, 'pause_button'):
                self.ui_manager.pause_button.config(text=pause_button_text)
                
            self.logger.info("热键显示已更新")
            
        except Exception as e:
            self.logger.error(f"更新热键显示失败: {e}")
    
    def _check_and_display_hotkey_conflicts(self):
        """检查热键冲突并在界面上显示警告"""
        try:
            current_hotkeys = self.config.get_hotkeys()
            conflicts = []
            
            # 检查每个热键是否可能有冲突
            for hotkey_name, hotkey_combo in current_hotkeys.items():
                if self._is_hotkey_potentially_conflicted(hotkey_combo):
                    conflicts.append((hotkey_name, hotkey_combo))
            
            if conflicts:
                # 在状态栏显示冲突警告
                conflict_info = []
                for name, combo in conflicts:
                    if name == 'select_region':
                        conflict_info.append(f"选择区域({combo})")
                    elif name == 'quick_capture':
                        conflict_info.append(f"快速采集({combo})")
                    elif name == 'pause_capture':
                        conflict_info.append(f"暂停({combo})")
                
                if conflict_info:
                    warning_msg = f"⚠️ 可能的热键冲突: {', '.join(conflict_info)}"
                    
                    # 在界面上显示警告
                    if self.ui_manager and hasattr(self.ui_manager, 'status_label'):
                        self.ui_manager.status_label.config(text=warning_msg, foreground="#e67e22")
                    else:
                        self.logger.warning(f"热键冲突检测: {warning_msg}")
            
        except Exception as e:
            self.logger.error(f"热键冲突检测失败: {e}")
    
    def _is_hotkey_potentially_conflicted(self, hotkey_combo: str) -> bool:
        """检查热键是否可能与系统或其他程序冲突"""
        # 常见冲突的热键组合
        common_conflicts = [
            'ctrl+alt+p', 'ctrl+alt+s', 'ctrl+alt+n', 'ctrl+alt+b', 'space',
            'ctrl+alt+delete', 'ctrl+shift+esc', 'win+l', 'win+d', 'win+r',
            'alt+tab', 'alt+f4', 'ctrl+alt+t', 'ctrl+alt+z', 'ctrl+shift+a',
            'f12', 'ctrl+shift+i', 'printscreen', 'alt+printscreen', 'ctrl+alt+a'
        ]
        
        return hotkey_combo.lower() in [conflict.lower() for conflict in common_conflicts]
    
    def _check_hotkey_permissions(self):
        """检查热键权限和监听状态"""
        if self.hotkey_listening_failed:
            error_msg = "⚠️ 热键监听失败"
            if not self.is_admin:
                error_msg += " (建议以管理员身份运行)"
            
            if self.ui_manager and hasattr(self.ui_manager, 'status_label'):
                self.ui_manager.status_label.config(text=error_msg, foreground="#e74c3c")
    
    def open_data_directory(self):
        """打开数据目录"""
        data_path = self.data_manager.images_dir
        if data_path.exists():
            if platform.system() == "Windows":
                subprocess.run(["explorer", str(data_path)])
            elif platform.system() == "Darwin":
                subprocess.run(["open", str(data_path)])
            else:
                subprocess.run(["xdg-open", str(data_path)])
        else:
            messagebox.showinfo("提示", f"数据目录不存在：{data_path}")
    
    def open_system_settings(self):
        """打开系统设置对话框"""
        try:
            # 创建系统设置对话框
            dialog = SystemSettingsDialog(
                self.root, 
                self.config, 
                self._on_system_settings_saved
            )
            
        except Exception as e:
            self.logger.error(f"打开系统设置失败: {e}")
            messagebox.showerror("错误", f"打开系统设置失败: {e}")
    
    def _on_system_settings_saved(self):
        """系统设置保存后的回调"""
        try:
            # 重新加载配置
            self.config = DataCollectorConfig()
            
            # 检查管理员权限设置变化
            admin_required = self.config.get_run_as_admin()
            if admin_required and not self.is_admin:
                # 如果设置为需要管理员权限但当前不是管理员，提示重启
                result = messagebox.askyesno(
                    "重启程序",
                    "管理员权限设置已更改。\n\n"
                    "是否立即重启程序以应用新设置？\n"
                    "（选择'否'将在下次启动时生效）"
                )
                if result:
                    self._restart_as_admin()
            
            self.logger.info("系统设置已更新")
            
        except Exception as e:
            self.logger.error(f"应用系统设置失败: {e}")
    
    def _restart_as_admin(self):
        """以管理员身份重启程序"""
        try:
            from .admin_utils import run_as_admin
            
            # 保存当前状态（如果需要）
            self.cleanup()
            
            # 以管理员身份重启
            if run_as_admin():
                # 成功启动管理员版本，退出当前进程
                self.root.quit()
                sys.exit(0)
            else:
                messagebox.showerror("错误", "无法以管理员身份重启程序")
                
        except Exception as e:
            self.logger.error(f"重启程序失败: {e}")
            messagebox.showerror("错误", f"重启程序失败: {e}")
    
    def open_category_folder(self, category: str):
        """打开指定类别的文件夹"""
        category_path = self.data_manager.images_dir / category
        if category_path.exists():
            try:
                if platform.system() == "Windows":
                    subprocess.run(["explorer", str(category_path)])
                elif platform.system() == "Darwin":
                    subprocess.run(["open", str(category_path)])
                else:
                    subprocess.run(["xdg-open", str(category_path)])
                self.logger.info(f"打开类别文件夹: {category}")
            except Exception as e:
                self.logger.error(f"打开文件夹失败: {e}")
                messagebox.showerror("错误", f"无法打开文件夹: {e}")
        else:
            messagebox.showinfo("提示", f"类别文件夹不存在：{category}")
    
    def select_target_region_and_category(self):
        """选择截图区域并设置类别"""
        def region_callback(region):
            if region:
                self.current_target_region = region
                category = simpledialog.askstring("设置类别", 
                                                 "请输入图像类别名称:\n(例如: fish_hooked, car_red, ui_button)")
                
                if category and category.strip():
                    category = category.strip()
                    if self.data_manager.validate_category_name(category):
                        self.current_category = category
                        
                        # 设置类别计数器（支持增量采集）
                        current_count = self.data_manager.setup_category_counter(category)
                        
                        # 更新界面显示
                        if self.ui_manager:
                            if current_count > 0:
                                self.ui_manager.category_label.config(
                                    text=f"{self.current_category} (继续: {current_count}张)", 
                                    style="Success.TLabel"
                                )
                                messagebox.showinfo("增量采集", 
                                                   f"检测到类别 '{category}' 已有 {current_count} 张图片\n"
                                                   f"将从编号 {current_count + 1} 开始继续采集")
                            else:
                                self.ui_manager.category_label.config(text=self.current_category, style="Success.TLabel")
                            
                            # 启用快速截图按钮
                            self.ui_manager.capture_button.config(state="normal")
                        
                        # 启用热键
                        if self.hotkey_listener:
                            self.hotkey_listener.enable_capture()
                        
                        self.logger.info(f"设置类别: {self.current_category}, 区域: {region}")
                    else:
                        messagebox.showerror("错误", "类别名包含非法字符！")
        
        self.screen_capture.select_region(region_callback)
    
    def toggle_capture_pause(self):
        """切换截图暂停状态"""
        self.capture_paused = not self.capture_paused
        
        if self.capture_paused:
            # 暂停截图功能
            if self.hotkey_listener:
                self.hotkey_listener.pause_capture()
            if self.ui_manager:
                pause_hotkey = self.format_hotkey_display(self.config.get('hotkeys.pause_capture', 'ctrl+alt+p'))
                self.ui_manager.pause_button.config(text=f"▶️ 恢复 ({pause_hotkey})")
            self.logger.info("截图功能已暂停")
        else:
            # 恢复截图功能
            if self.hotkey_listener:
                self.hotkey_listener.resume_capture()
            if self.ui_manager:
                pause_hotkey = self.format_hotkey_display(self.config.get('hotkeys.pause_capture', 'ctrl+alt+p'))
                self.ui_manager.pause_button.config(text=f"⏸️ 暂停 ({pause_hotkey})")
            self.logger.info("截图功能已恢复")
    
    def quick_capture_fullscreen(self):
        """快速全屏采集（YOLO数据采集模式）"""
        if not self.current_target_region or not self.current_category:
            messagebox.showwarning("警告", "请先选择目标区域并设置类别！")
            return
        
        if self.capture_paused:
            messagebox.showwarning("警告", "采集功能已暂停，请先恢复")
            return
        
        try:
            # 执行全屏截图
            fullscreen_image = self.screen_capture.capture_fullscreen()
            if fullscreen_image:
                # 保存全屏图像和YOLO标注文件
                image_path, label_path = self.data_manager.save_fullscreen_with_annotation(
                    fullscreen_image, 
                    self.current_category,
                    self.current_target_region,
                    self.config.get('image.format', 'jpg'),
                    self.config.get('image.quality', 95)
                )
                
                if image_path and label_path:
                    # 更新预览（显示带目标框的预览）
                    self.update_preview_with_target_box(fullscreen_image)
                    
                    # 更新统计信息
                    self.update_statistics()
                    
                    # 显示成功信息
                    count = self.data_manager.get_category_count(self.current_category)
                    self.logger.info(f"成功采集全屏数据: {image_path} + {label_path} (类别总数: {count})")
                else:
                    messagebox.showerror("错误", "保存YOLO数据失败")
            else:
                messagebox.showerror("错误", "全屏截图失败")
                
        except Exception as e:
            self.logger.error(f"快速采集失败: {e}")
            messagebox.showerror("错误", f"快速采集失败: {e}")
    
    def update_preview_with_target_box(self, image: Image.Image):
        """更新预览图像（显示带目标框的预览）"""
        try:
            # 创建预览图像的副本
            preview_image = image.copy()
            
            # 在预览图像上绘制目标区域框
            if self.current_target_region:
                draw = ImageDraw.Draw(preview_image)
                
                left = self.current_target_region['left']
                top = self.current_target_region['top']
                right = left + self.current_target_region['width']
                bottom = top + self.current_target_region['height']
                
                # 绘制红色矩形框
                draw.rectangle([left, top, right, bottom], outline='red', width=4)
                
                # 添加类别标签
                if self.current_category:
                    try:
                        font = ImageFont.truetype("arial.ttf", 20)
                    except:
                        font = ImageFont.load_default()
                    
                    # 绘制背景矩形
                    text_bbox = draw.textbbox((0, 0), self.current_category, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]
                    
                    # 调整标签位置，避免超出图像边界
                    label_x = max(0, left)
                    label_y = max(0, top - text_height - 5)
                    
                    # 绘制标签背景
                    draw.rectangle([label_x, label_y, label_x + text_width + 6, label_y + text_height + 2], 
                                 fill='red', outline='red')
                    
                    # 绘制标签文字
                    draw.text((label_x + 3, label_y + 1), self.current_category, fill='white', font=font)
            
            # 更新UI预览
            if self.ui_manager:
                self.ui_manager.update_preview(preview_image)
            
        except Exception as e:
            self.logger.error(f"更新带目标框的预览失败: {e}")
            # 回退到普通预览
            if self.ui_manager:
                self.ui_manager.update_preview(image)
    
    def update_statistics(self):
        """更新统计信息"""
        try:
            # 获取图像统计
            stats = self.data_manager.get_statistics()
            total_images = sum(stats.values())
            total_categories = len(stats)
            
            # 获取标注统计
            annotation_info = self.data_manager.get_annotation_info()
            total_annotations = annotation_info['total_annotations']
            
            # 更新UI统计信息
            if self.ui_manager:
                self.ui_manager.total_stats_label.config(text=f"总计: {total_categories} 个类别, {total_images} 张图片")
                self.ui_manager.annotation_stats_label.config(text=f"标注: {total_annotations} 个标注文件")
                
                # 清除现有类别标签
                for widget in self.ui_manager.stats_scrollable_frame.winfo_children():
                    widget.destroy()
                
                # 创建类别统计显示
                self._create_category_stats(stats, annotation_info)
            
            self.logger.info(f"统计信息已更新: {total_categories}个类别, {total_images}张图片")
            
        except Exception as e:
            self.logger.error(f"更新统计失败: {e}")
    
    def _create_category_stats(self, stats, annotation_info):
        """创建类别统计显示"""
        if not self.ui_manager:
            return
            
        if stats:
            # 按图片数量降序排列
            sorted_categories = sorted(stats.items(), key=lambda x: x[1], reverse=True)
            
            for category, count in sorted_categories:
                self._create_category_item(category, count, annotation_info)
        else:
            # 无数据时的提示
            self._create_no_data_display()
    
    def _create_category_item(self, category, count, annotation_info):
        """创建单个类别项"""
        from tkinter import ttk
        
        # 创建类别框架（可点击）
        category_frame = ttk.Frame(self.ui_manager.stats_scrollable_frame, relief="ridge", padding="6")
        category_frame.pack(fill="x", pady=2, padx=8)
        category_frame.configure(cursor="hand2")
        
        # 标注数量标签
        annotation_count = annotation_info['categories'].get(category, 0)
        ann_label = ttk.Label(category_frame, 
                            text=f"标注:{annotation_count}",
                            font=('Microsoft YaHei', 9),
                            foreground="#3498db",
                            width=8,
                            anchor="center",
                            cursor="hand2")
        ann_label.pack(side="right", padx=(5, 2))
        
        # 数量标签
        count_label = ttk.Label(category_frame, 
                               text=f"{count} 张",
                               font=('Microsoft YaHei', 10, 'bold'),
                               foreground="#27ae60",
                               width=8,
                               anchor="center",
                               cursor="hand2")
        count_label.pack(side="right", padx=(5, 5))
        
        # 类别ID标签
        class_id = self.data_manager.class_mapping.get(category, 'N/A')
        id_label = ttk.Label(category_frame, text=f"ID:{class_id}", 
                           font=('Microsoft YaHei', 9), 
                           foreground="#7f8c8d",
                           width=6,
                           cursor="hand2")
        id_label.pack(side="right", padx=(5, 10))
        
        # 类别名标签
        display_name = category if len(category) <= 12 else f"{category[:9]}..."
        category_label = ttk.Label(category_frame, 
                                  text=f"📁 {display_name}",
                                  font=('Microsoft YaHei', 10),
                                  foreground="#2c3e50",
                                  cursor="hand2")
        category_label.pack(side="left", fill="x", expand=True, padx=(2, 5))
        
        # 为当前类别添加高亮
        if category == self.current_category:
            category_frame.configure(style="Highlight.TFrame")
            category_label.configure(foreground="#27ae60", font=('Microsoft YaHei', 10, 'bold'))
            count_label.configure(foreground="#27ae60")
            ann_label.configure(foreground="#27ae60")
            id_label.configure(foreground="#27ae60")
        
        # 绑定点击事件
        for widget in [category_frame, category_label, count_label, ann_label, id_label]:
            widget.bind("<Button-1>", lambda e, cat=category: self.open_category_folder(cat))
    
    def _create_no_data_display(self):
        """创建无数据显示"""
        from tkinter import ttk
        
        no_data_frame = ttk.Frame(self.ui_manager.stats_scrollable_frame, padding="20")
        no_data_frame.pack(fill="both", expand=True)
        
        ttk.Label(no_data_frame, text="🔍 暂无数据", 
                 font=('Microsoft YaHei', 13), 
                 foreground="#95a5a6").pack()
        ttk.Label(no_data_frame, text="开始截图收集数据吧！", 
                 font=('Microsoft YaHei', 11), 
                 foreground="#7f8c8d").pack(pady=(5, 0))
    
    def cleanup(self):
        """清理资源"""
        try:
            self.logger.info("正在关闭数据采集工具")
            if self.hotkey_listener:
                self.hotkey_listener.stop_listening()
            self.data_manager.cleanup_empty_directories()
        except Exception as e:
            self.logger.error(f"清理资源异常: {e}")
    
    def initialize_permissions_check(self):
        """初始化权限检查"""
        self._check_hotkey_permissions() 