"""
桌面测试工具
提供实时的模型推理测试界面
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cv2
import numpy as np
from PIL import Image, ImageTk
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from modules.logger import setup_logger, LogContext

# 修复相对导入问题
try:
    from .model_validator import ModelValidator
except ImportError:
    # 当作为独立脚本运行时，使用绝对导入
    from modules.model_trainer.model_validator import ModelValidator

try:
    from ultralytics import YOLO
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False

try:
    import mss
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False

class DesktopTesterApp:
    """桌面测试工具主应用"""
    
    def __init__(self):
        """初始化桌面测试应用"""
        self.logger = setup_logger('DesktopTesterApp')
        
        # 检查依赖
        if not ULTRALYTICS_AVAILABLE:
            self.logger.error("Ultralytics YOLO库未安装")
            raise ImportError("需要安装ultralytics库")
        
        # 核心组件
        self.model_validator = ModelValidator()
        
        # 界面变量
        self.root = None
        self.canvas = None
        self.results_text = None
        
        # 模型相关
        self.current_model = None
        self.model_path = ""
        
        # 测试相关
        self.test_image = None
        self.test_image_path = ""
        self.confidence_threshold = 0.5
        
        # 实时测试
        self.is_realtime_testing = False
        self.realtime_thread = None
        self.screen_capture = mss.mss() if MSS_AVAILABLE else None
        
    def run(self):
        """启动桌面测试应用"""
        with LogContext(self.logger, "启动桌面测试应用"):
            self.create_main_window()
            # 在界面创建完成后自动检测并加载最新模型
            self.auto_load_latest_model()
            self.root.mainloop()
    
    def create_main_window(self):
        """创建主窗口"""
        self.root = tk.Tk()
        self.root.title("🖥️ YOLO模型桌面测试工具 v2.3")
        self.root.geometry("1600x1000")
        self.root.resizable(True, True)
        
        # 设置最小窗口大小
        self.root.minsize(1400, 900)
        
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建左侧控制面板
        self.create_control_panel(main_frame)
        
        # 创建右侧显示区域
        self.create_display_area(main_frame)
        
        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def auto_load_latest_model(self):
        """自动检测并加载fishing_model_latest.pt模型"""
        try:
            # 检查runs目录下是否存在fishing_model_latest.pt
            runs_model_path = Path("runs/fishing_model_latest.pt")
            model_dir_path = Path("model/fishing_model_latest.pt")
            
            # 优先检查runs目录，再检查model目录
            target_path = None
            if runs_model_path.exists():
                target_path = runs_model_path
            elif model_dir_path.exists():
                target_path = model_dir_path
            
            if target_path:
                # 加载模型
                self.current_model = YOLO(str(target_path))
                self.model_path = str(target_path)
                
                # 更新显示
                self.model_path_var.set(f"fishing_model_latest.pt (自动检测)")
                
                # 启用测试按钮
                self.test_btn.config(state=tk.NORMAL)
                
                self.logger.info(f"自动加载模型: {target_path}")
                
        except Exception as e:
            self.logger.warning(f"自动加载最新模型失败: {str(e)}")
    
    def create_control_panel(self, parent):
        """创建左侧控制面板"""
        control_frame = ttk.LabelFrame(parent, text="控制面板", padding="10")
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        
        # 设置控制面板固定宽度
        control_frame.config(width=350)
        
        # 模型选择区域
        model_frame = ttk.LabelFrame(control_frame, text="模型设置", padding="10")
        model_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 模型路径显示
        ttk.Label(model_frame, text="当前模型:").pack(anchor=tk.W)
        self.model_path_var = tk.StringVar(value="未选择模型")
        model_label = ttk.Label(model_frame, textvariable=self.model_path_var, 
                               font=("Arial", 9), foreground="blue")
        model_label.pack(anchor=tk.W, fill=tk.X)
        
        # 选择模型按钮
        ttk.Button(model_frame, text="📁 选择模型", 
                  command=self.select_model).pack(fill=tk.X, pady=2)
        
        # 参数设置区域
        params_frame = ttk.LabelFrame(control_frame, text="参数设置", padding="10")
        params_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 置信度阈值
        ttk.Label(params_frame, text="置信度阈值:").pack(anchor=tk.W)
        self.confidence_var = tk.DoubleVar(value=0.5)
        confidence_scale = ttk.Scale(params_frame, from_=0.1, to=1.0, 
                                   variable=self.confidence_var, orient=tk.HORIZONTAL)
        confidence_scale.pack(fill=tk.X, pady=2)
        
        # 置信度显示
        self.confidence_label = ttk.Label(params_frame, text="0.50")
        self.confidence_label.pack(anchor=tk.W)
        
        # 绑定置信度变化
        self.confidence_var.trace('w', self.update_confidence_label)
        
        # 测试模式选择
        mode_frame = ttk.LabelFrame(control_frame, text="测试模式", padding="10")
        mode_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.test_mode = tk.StringVar(value="single")
        ttk.Radiobutton(mode_frame, text="单张图片测试", variable=self.test_mode, 
                       value="single").pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="批量图片测试", variable=self.test_mode, 
                       value="batch").pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="实时屏幕测试", variable=self.test_mode, 
                       value="realtime").pack(anchor=tk.W)
        
        # 操作按钮区域
        ops_frame = ttk.LabelFrame(control_frame, text="操作", padding="10")
        ops_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 加载图片按钮
        ttk.Button(ops_frame, text="📷 加载图片", 
                  command=self.load_image).pack(fill=tk.X, pady=2)
        
        # 测试按钮
        self.test_btn = ttk.Button(ops_frame, text="🚀 开始测试", 
                                  command=self.start_test, state=tk.DISABLED)
        self.test_btn.pack(fill=tk.X, pady=2)
        
        # 停止按钮
        self.stop_btn = ttk.Button(ops_frame, text="⏹️ 停止测试", 
                                  command=self.stop_test, state=tk.DISABLED)
        self.stop_btn.pack(fill=tk.X, pady=2)
        
        # 清除结果按钮
        ttk.Button(ops_frame, text="🗑️ 清除结果", 
                  command=self.clear_results).pack(fill=tk.X, pady=2)
        
        # 保存结果按钮
        ttk.Button(ops_frame, text="💾 保存结果", 
                  command=self.save_results).pack(fill=tk.X, pady=2)
        
        # 状态显示区域
        status_frame = ttk.LabelFrame(control_frame, text="状态信息", padding="10")
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_text = tk.Text(status_frame, height=5, wrap=tk.WORD, 
                                  font=("Arial", 9))
        status_scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, 
                                       command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=status_scrollbar.set)
        
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        status_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_display_area(self, parent):
        """创建右侧显示区域"""
        display_frame = ttk.Frame(parent)
        display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # 上方图像显示区域
        image_frame = ttk.LabelFrame(display_frame, text="图像显示", padding="10")
        image_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # 图片信息栏
        info_frame = ttk.Frame(image_frame)
        info_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.image_info_var = tk.StringVar(value="未加载图片")
        ttk.Label(info_frame, textvariable=self.image_info_var, 
                 font=("Arial", 9), foreground="gray").pack(anchor=tk.W)
        
        # 创建画布 - 增大默认尺寸
        self.canvas = tk.Canvas(image_frame, bg='white', width=900, height=600)
        canvas_scrollbar_v = ttk.Scrollbar(image_frame, orient=tk.VERTICAL, 
                                         command=self.canvas.yview)
        canvas_scrollbar_h = ttk.Scrollbar(image_frame, orient=tk.HORIZONTAL, 
                                         command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=canvas_scrollbar_v.set,
                            xscrollcommand=canvas_scrollbar_h.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas_scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y)
        canvas_scrollbar_h.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 下方结果显示区域
        results_frame = ttk.LabelFrame(display_frame, text="检测结果", padding="10")
        results_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 创建结果表格 - 减少高度给图片更多空间
        self.results_tree = ttk.Treeview(results_frame, 
                                       columns=('bbox', 'confidence', 'class'), 
                                       show='tree headings', height=6)
        self.results_tree.heading('#0', text='序号')
        self.results_tree.heading('bbox', text='边界框')
        self.results_tree.heading('confidence', text='置信度')
        self.results_tree.heading('class', text='类别')
        
        # 设置列宽
        self.results_tree.column('#0', width=50)
        self.results_tree.column('bbox', width=200)
        self.results_tree.column('confidence', width=100)
        self.results_tree.column('class', width=200)
        
        results_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, 
                                        command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=results_scrollbar.set)
        
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def select_model(self):
        """选择模型文件"""
        file_path = filedialog.askopenfilename(
            title="选择YOLO模型文件",
            filetypes=[("YOLO模型", "*.pt"), ("所有文件", "*.*")],
            initialdir="model"
        )
        
        if file_path:
            try:
                # 加载模型
                self.current_model = YOLO(file_path)
                self.model_path = file_path
                
                # 更新显示
                model_name = Path(file_path).name
                self.model_path_var.set(model_name)
                
                # 启用测试按钮
                self.test_btn.config(state=tk.NORMAL)
                
                self.log_status(f"已加载模型: {model_name}")
                
            except Exception as e:
                self.log_status(f"加载模型失败: {str(e)}", "ERROR")
                messagebox.showerror("错误", f"加载模型失败:\n{str(e)}")
    
    def load_image(self):
        """加载测试图片"""
        file_path = filedialog.askopenfilename(
            title="选择测试图片",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp"), ("所有文件", "*.*")],
            initialdir="runs"
        )
        
        if file_path:
            try:
                # 加载图片
                self.test_image = Image.open(file_path)
                self.test_image_path = file_path
                
                # 显示图片
                self.display_image(self.test_image)
                
                self.log_status(f"已加载图片: {Path(file_path).name}")
                
            except Exception as e:
                self.log_status(f"加载图片失败: {str(e)}", "ERROR")
                messagebox.showerror("错误", f"加载图片失败:\n{str(e)}")
    
    def display_image(self, image: Image.Image, detections: List[Dict] = None):
        """
        在画布上显示图片和检测结果
        
        Args:
            image: 要显示的图片
            detections: 检测结果列表
        """
        try:
            # 清空画布
            self.canvas.delete("all")
            
            # 调整图片尺寸以适应画布
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                # 画布尚未初始化，使用默认尺寸
                canvas_width, canvas_height = 900, 600
            
            # 计算缩放比例 - 允许适度放大小图片
            img_width, img_height = image.size
            scale_w = (canvas_width - 20) / img_width  # 留出边距
            scale_h = (canvas_height - 20) / img_height
            
            # 智能缩放策略
            if img_width < 400 or img_height < 300:
                # 小图片允许放大到合适大小，但不超过2倍
                scale = min(scale_w, scale_h, 2.0)
            else:
                # 大图片按需缩小，或轻微放大
                scale = min(scale_w, scale_h, 1.2)
            
            # 缩放图片
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            display_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 转换为Tkinter格式
            self.photo = ImageTk.PhotoImage(display_image)
            
            # 在画布中心显示图片
            x = (canvas_width - new_width) // 2
            y = (canvas_height - new_height) // 2
            self.canvas.create_image(x, y, anchor=tk.NW, image=self.photo)
            
            # 更新图片信息显示
            scale_percent = int(scale * 100)
            info_text = f"原始尺寸: {img_width}×{img_height} | 显示尺寸: {new_width}×{new_height} | 缩放: {scale_percent}%"
            self.image_info_var.set(info_text)
            
            # 绘制检测框
            if detections:
                self.draw_detections(detections, scale, x, y)
            
        except Exception as e:
            self.log_status(f"显示图片失败: {str(e)}", "ERROR")
    
    def draw_detections(self, detections: List[Dict], scale: float, offset_x: int, offset_y: int):
        """
        绘制检测框
        
        Args:
            detections: 检测结果列表
            scale: 缩放比例
            offset_x: X偏移
            offset_y: Y偏移
        """
        colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
        
        for idx, detection in enumerate(detections):
            bbox = detection['bbox']
            confidence = detection['confidence']
            class_name = detection.get('chinese_name', detection['class_name'])
            
            # 计算缩放后的坐标
            x1, y1, x2, y2 = bbox
            x1 = int(x1 * scale) + offset_x
            y1 = int(y1 * scale) + offset_y
            x2 = int(x2 * scale) + offset_x
            y2 = int(y2 * scale) + offset_y
            
            # 选择颜色
            color = colors[idx % len(colors)]
            
            # 绘制边界框
            self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=2)
            
            # 绘制标签
            label = f"{class_name} {confidence:.2f}"
            self.canvas.create_text(x1, y1-10, anchor=tk.SW, text=label, 
                                  fill=color, font=("Arial", 10, "bold"))
    
    def start_test(self):
        """开始测试"""
        if not self.current_model:
            messagebox.showwarning("警告", "请先选择模型")
            return
        
        mode = self.test_mode.get()
        confidence = self.confidence_var.get()
        
        if mode == "single":
            self.test_single_image(confidence)
        elif mode == "batch":
            self.test_batch_images(confidence)
        elif mode == "realtime":
            self.start_realtime_test(confidence)
    
    def test_single_image(self, confidence: float):
        """测试单张图片"""
        if not self.test_image_path:
            messagebox.showwarning("警告", "请先加载测试图片")
            return
        
        try:
            self.log_status("开始单张图片测试...")
            
            # 执行推理
            results = self.current_model(self.test_image_path, conf=confidence, verbose=False)
            
            if results:
                result = results[0]
                detections = self._extract_detections(result)
                
                # 显示结果
                self.display_image(self.test_image, detections)
                self.display_detection_results(detections)
                
                self.log_status(f"检测完成，发现 {len(detections)} 个目标")
            else:
                self.log_status("推理失败", "ERROR")
                
        except Exception as e:
            self.log_status(f"单张测试失败: {str(e)}", "ERROR")
    
    def test_batch_images(self, confidence: float):
        """批量测试图片"""
        dir_path = filedialog.askdirectory(title="选择图片目录", initialdir="runs")
        if not dir_path:
            return
        
        try:
            self.log_status("开始批量测试...")
            
            # 在新线程中执行批量测试
            def batch_test_thread():
                results = self.model_validator.batch_test_images(
                    self.model_path, dir_path, confidence
                )
                
                # 统计结果
                total_images = len(results)
                total_detections = sum(len(r.get('detections', [])) for r in results if 'detections' in r)
                
                self.root.after(0, lambda: self.log_status(
                    f"批量测试完成: {total_images} 张图片, {total_detections} 个检测"
                ))
            
            threading.Thread(target=batch_test_thread, daemon=True).start()
            
        except Exception as e:
            self.log_status(f"批量测试失败: {str(e)}", "ERROR")
    
    def start_realtime_test(self, confidence: float):
        """开始实时测试"""
        if not MSS_AVAILABLE:
            messagebox.showerror("错误", "实时测试需要安装mss库:\npip install mss")
            return
        
        try:
            self.is_realtime_testing = True
            self.test_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            
            # 启动实时测试线程
            self.realtime_thread = threading.Thread(
                target=self._realtime_test_thread,
                args=(confidence,),
                daemon=True
            )
            self.realtime_thread.start()
            
            self.log_status("实时测试已启动")
            
        except Exception as e:
            self.log_status(f"启动实时测试失败: {str(e)}", "ERROR")
    
    def _realtime_test_thread(self, confidence: float):
        """实时测试线程"""
        try:
            # 获取主显示器信息
            monitor = self.screen_capture.monitors[1]  # 主显示器
            
            while self.is_realtime_testing:
                try:
                    # 截取屏幕
                    screenshot = self.screen_capture.grab(monitor)
                    
                    # 转换为PIL图像
                    img_array = np.array(screenshot)
                    img_rgb = img_array[:, :, [2, 1, 0]]  # BGRA -> RGB
                    pil_image = Image.fromarray(img_rgb)
                    
                    # 执行推理
                    results = self.current_model(img_array, conf=confidence, verbose=False)
                    
                    if results:
                        result = results[0]
                        detections = self._extract_detections(result)
                        
                        # 更新显示 (在主线程中)
                        self.root.after(0, lambda img=pil_image, det=detections: 
                                      self.display_image(img, det))
                        self.root.after(0, lambda det=detections: 
                                      self.display_detection_results(det))
                    
                    # 控制帧率
                    time.sleep(0.1)  # 10 FPS
                    
                except Exception as e:
                    self.root.after(0, lambda: self.log_status(f"实时测试错误: {str(e)}", "ERROR"))
                    break
                    
        except Exception as e:
            self.root.after(0, lambda: self.log_status(f"实时测试线程错误: {str(e)}", "ERROR"))
        finally:
            self.is_realtime_testing = False
            self.root.after(0, lambda: self.test_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))
    
    def stop_test(self):
        """停止测试"""
        self.is_realtime_testing = False
        self.test_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log_status("测试已停止")
    
    def _extract_detections(self, result) -> List[Dict]:
        """从YOLO结果中提取检测信息"""
        detections = []
        
        if result.boxes is not None:
            for box in result.boxes:
                # 获取边界框坐标
                coords = box.xyxy[0].cpu().numpy()
                
                # 获取置信度和类别
                confidence = float(box.conf[0].cpu().numpy())
                class_id = int(box.cls[0].cpu().numpy())
                
                detection = {
                    'bbox': coords.tolist(),
                    'confidence': confidence,
                    'class_id': class_id,
                    'class_name': self.model_validator.class_names.get(class_id, f"Unknown_{class_id}"),
                    'chinese_name': self.model_validator.chinese_names.get(class_id, f"未知_{class_id}")
                }
                detections.append(detection)
        
        return detections
    
    def display_detection_results(self, detections: List[Dict]):
        """显示检测结果到表格"""
        # 清空现有结果
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # 添加新结果
        for idx, detection in enumerate(detections):
            bbox_str = f"({detection['bbox'][0]:.0f}, {detection['bbox'][1]:.0f}, " \
                      f"{detection['bbox'][2]:.0f}, {detection['bbox'][3]:.0f})"
            confidence_str = f"{detection['confidence']:.3f}"
            class_str = f"{detection['chinese_name']} ({detection['class_name']})"
            
            self.results_tree.insert('', 'end', text=str(idx+1),
                                    values=(bbox_str, confidence_str, class_str))
    
    def clear_results(self):
        """清除检测结果"""
        # 清空画布
        self.canvas.delete("all")
        
        # 清空结果表格
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # 清空状态日志
        self.status_text.delete(1.0, tk.END)
        
        self.log_status("结果已清除")
    
    def save_results(self):
        """保存检测结果"""
        messagebox.showinfo("保存结果", "保存功能开发中...")
    
    def update_confidence_label(self, *args):
        """更新置信度标签"""
        confidence = self.confidence_var.get()
        self.confidence_label.config(text=f"{confidence:.2f}")
    
    def log_status(self, message: str, level: str = "INFO"):
        """记录状态日志"""
        timestamp = time.strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {level}: {message}\n"
        
        self.status_text.insert(tk.END, log_line)
        self.status_text.see(tk.END)
        
        # 限制日志长度
        if int(self.status_text.index('end-1c').split('.')[0]) > 100:
            self.status_text.delete(1.0, "20.0")
    
    def on_closing(self):
        """窗口关闭事件"""
        if self.is_realtime_testing:
            self.stop_test()
        
        self.root.destroy()

def main():
    """主入口函数"""
    try:
        app = DesktopTesterApp()
        app.run()
    except Exception as e:
        print(f"启动桌面测试工具失败: {str(e)}")

if __name__ == "__main__":
    main() 