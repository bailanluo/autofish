"""
屏幕截图模块 v2.1 - 全屏YOLO数据采集
提供全屏截图和目标区域选择功能
"""

import tkinter as tk
from typing import Dict, Optional, Callable
from PIL import Image
import mss
import numpy as np
import sys
import os
import ctypes

# 添加主项目路径以使用logger
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from modules.logger import setup_logger, LogContext


class ScreenCapture:
    """屏幕截图工具类 - 支持全屏截图和目标区域标注"""
    
    def __init__(self):
        """初始化截图工具"""
        self.logger = setup_logger('ScreenCapture')  # 日志记录器
        self.sct = mss.mss()  # MSS截图对象
        
    def capture_fullscreen(self) -> Optional[Image.Image]:
        """
        截取全屏图像
        
        Returns:
            PIL Image对象，失败返回None
        """
        try:
            with LogContext(self.logger, "全屏截图"):
                # 重新创建MSS对象以避免线程问题
                with mss.mss() as sct:
                    # 获取主显示器全屏
                    monitor = sct.monitors[1]  # 主显示器
                    
                    # 执行截图
                    screenshot = sct.grab(monitor)
                    
                    # 转换为PIL Image（兼容性更好的方法）
                    # 将MSS的BGRA数据转换为RGB数组
                    img_array = np.array(screenshot)
                    # 转换BGRA到RGB（去掉Alpha通道并调整颜色顺序）
                    img_rgb = img_array[:, :, [2, 1, 0]]  # BGR -> RGB
                    image = Image.fromarray(img_rgb)
                    
                    self.logger.info(f"成功截取全屏图像: {image.size}")
                    return image
                
        except Exception as e:
            self.logger.error(f"全屏截图失败: {e}")
            return None
    
    def capture_screen(self, region: Optional[Dict] = None) -> Optional[Image.Image]:
        """
        截取屏幕区域（向后兼容方法）
        
        Args:
            region: 截图区域 {'top': y, 'left': x, 'width': w, 'height': h}
            如果为None，则进行全屏截图
            
        Returns:
            PIL Image对象，失败返回None
        """
        if region is None:
            return self.capture_fullscreen()
        
        try:
            with LogContext(self.logger, "区域截图"):
                # 重新创建MSS对象以避免线程问题
                with mss.mss() as sct:
                    # 执行截图
                    screenshot = sct.grab(region)
                    
                    # 转换为PIL Image
                    img_array = np.array(screenshot)
                    img_rgb = img_array[:, :, [2, 1, 0]]  # BGR -> RGB
                    image = Image.fromarray(img_rgb)
                    
                    self.logger.info(f"成功截取区域图像: {region}")
                    return image
                
        except Exception as e:
            self.logger.error(f"区域截图失败: {e}")
            return None
    
    def select_target_region(self, callback: Callable) -> None:
        """
        打开目标区域选择界面（用于YOLO标注）
        
        Args:
            callback: 选择完成后的回调函数，接收target_region参数
        """
        TargetRegionSelector(callback)
    
    def select_region(self, callback: Callable) -> None:
        """向后兼容方法 - 重定向到目标区域选择"""
        self.select_target_region(callback)


class TargetRegionSelector:
    """目标区域选择器GUI - 用于YOLO标注"""
    
    def __init__(self, callback: Callable):
        """
        初始化目标区域选择器
        
        Args:
            callback: 选择完成后的回调函数
        """
        self.callback = callback  # 回调函数
        self.logger = setup_logger('TargetRegionSelector')  # 日志记录器
        
        # 设置DPI感知（仅Windows）
        self._set_dpi_awareness()
        
        # 获取真实屏幕尺寸（处理高DPI缩放）
        self.screen_width, self.screen_height = self._get_real_screen_size()
        
        # 创建全屏窗口
        self.root = tk.Toplevel()
        self.root.title("选择目标区域 - YOLO标注")
        
        # 设置窗口为真实屏幕尺寸
        self.root.geometry(f"{self.screen_width}x{self.screen_height}+0+0")
        self.root.overrideredirect(True)  # 移除窗口边框
        self.root.attributes('-alpha', 0.3)  # 半透明
        self.root.attributes('-topmost', True)  # 置顶
        self.root.configure(bg='black')  # 黑色背景
        
        self.logger.info(f"创建选择器窗口: {self.screen_width}x{self.screen_height}")
        
        # 创建画布
        self.canvas = tk.Canvas(self.root, cursor="cross", bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 绑定鼠标事件
        self.canvas.bind("<Button-1>", self.on_click)  # 鼠标按下
        self.canvas.bind("<B1-Motion>", self.on_drag)  # 鼠标拖拽
        self.canvas.bind("<ButtonRelease-1>", self.on_release)  # 鼠标释放
        
        # 绑定键盘事件
        self.root.bind("<Escape>", self.on_escape)  # ESC键取消
        self.root.focus_set()  # 获取焦点
        
        # 选择状态变量
        self.start_x = None  # 起始X坐标
        self.start_y = None  # 起始Y坐标
        self.rect_id = None  # 矩形对象ID
        
        # 显示提示文本
        self.show_instructions()
    
    def _set_dpi_awareness(self):
        """设置程序DPI感知，避免高DPI缩放问题"""
        try:
            # 设置为系统DPI感知（仅Windows）
            if sys.platform == "win32":
                ctypes.windll.user32.SetProcessDPIAware()
                self.logger.info("已设置DPI感知")
        except Exception as e:
            self.logger.warning(f"设置DPI感知失败: {e}")
    
    def _get_real_screen_size(self):
        """
        获取真实屏幕尺寸，处理高DPI缩放问题
        
        Returns:
            tuple: (width, height) 真实屏幕像素尺寸
        """
        try:
            # 方法1：使用Windows API获取真实屏幕尺寸
            user32 = ctypes.windll.user32
            screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
            self.logger.info(f"Windows API屏幕尺寸: {screensize}")
            
            # 方法2：使用MSS获取屏幕尺寸（更准确）
            with mss.mss() as sct:
                monitor = sct.monitors[1]  # 主显示器
                width = monitor['width']
                height = monitor['height']
                self.logger.info(f"MSS屏幕尺寸: {width}x{height}")
                return width, height
                
        except Exception as e:
            self.logger.warning(f"获取真实屏幕尺寸失败: {e}")
            # 回退到Tkinter方法
            root = tk.Tk()
            width = root.winfo_screenwidth()
            height = root.winfo_screenheight()
            root.destroy()
            self.logger.info(f"Tkinter屏幕尺寸: {width}x{height}")
            return width, height
        
    def show_instructions(self):
        """显示操作说明"""
        instructions = [
            "🎯 全屏YOLO数据采集模式",
            "",
            "📝 拖拽鼠标框选目标区域（用于生成YOLO标注）",
            "💾 松开鼠标后将保存全屏图片+标注文件", 
            "❌ 按ESC键取消选择"
        ]
        
        # 根据屏幕尺寸自适应字体大小
        font_size = max(16, int(self.screen_width / 120))  # 动态字体大小
        y_offset = max(50, int(self.screen_height / 30))   # 动态垂直偏移
        line_spacing = max(35, int(self.screen_height / 45))  # 动态行间距
        
        self.logger.info(f"字体设置: 大小={font_size}, 起始位置={y_offset}, 行间距={line_spacing}")
        
        for instruction in instructions:
            if instruction:  # 跳过空行
                self.canvas.create_text(
                    self.screen_width // 2, y_offset,
                    text=instruction, fill='white', font=('Microsoft YaHei', font_size, 'bold')
                )
            y_offset += line_spacing
    
    def on_click(self, event):
        """鼠标点击事件处理"""
        self.start_x = event.x
        self.start_y = event.y
        
        # 删除之前的矩形
        if self.rect_id:
            self.canvas.delete(self.rect_id)
    
    def on_drag(self, event):
        """鼠标拖拽事件处理"""
        if self.start_x is not None and self.start_y is not None:
            # 删除之前的矩形
            if self.rect_id:
                self.canvas.delete(self.rect_id)
            
            # 绘制新矩形（红色边框，半透明填充）
            self.rect_id = self.canvas.create_rectangle(
                self.start_x, self.start_y, event.x, event.y,
                outline='red', width=3, fill='red', stipple='gray25'
            )
    
    def on_release(self, event):
        """鼠标释放事件处理"""
        if self.start_x is not None and self.start_y is not None:
            # 计算选择区域
            x1, y1 = self.start_x, self.start_y
            x2, y2 = event.x, event.y
            
            # 确保左上角坐标更小
            left = min(x1, x2)
            top = min(y1, y2)
            width = abs(x2 - x1)
            height = abs(y2 - y1)
            
            # 检查区域大小
            if width < 10 or height < 10:
                self.logger.warning("目标区域太小，已取消")
                self.root.destroy()
                return
            
            # 创建目标区域字典
            target_region = {
                'left': left,
                'top': top,
                'width': width,
                'height': height
            }
            
            self.logger.info(f"选择目标区域: {target_region}")
            
            # 关闭窗口
            self.root.destroy()
            
            # 调用回调函数
            if self.callback:
                self.callback(target_region)
    
    def on_escape(self, event):
        """ESC键取消选择"""
        self.logger.info("用户取消目标区域选择")
        self.root.destroy()
        
        # 调用回调函数，传递None表示取消
        if self.callback:
            self.callback(None)


# 向后兼容的类别名
RegionSelector = TargetRegionSelector 