"""
Fisher钓鱼模块YOLO模型检测器
负责加载YOLO模型并识别钓鱼状态0-3和6

作者: AutoFish Team  
版本: v1.0
创建时间: 2024-12-28
"""

import cv2
import torch
import numpy as np
from typing import Optional, Tuple, List, Dict
from pathlib import Path
import mss
import logging
from ultralytics import YOLO

from .config import fisher_config

# 禁用ultralytics的详细日志输出
logging.getLogger('ultralytics').setLevel(logging.WARNING)


class ModelDetector:
    """YOLO模型检测器"""
    
    def __init__(self):
        """
        初始化模型检测器
        """
        self.model: Optional[YOLO] = None  # YOLO模型实例
        self.device: str = "cpu"  # 计算设备
        self.is_initialized: bool = False  # 初始化状态
        self.screenshot_tool = None  # 屏幕截图工具（延迟初始化）
        
        # 状态名称映射
        self.state_names = fisher_config.get_state_names()
        
        # 初始化模型
        self._initialize_model()
    
    def _initialize_model(self) -> bool:
        """
        初始化YOLO模型
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 获取模型路径
            model_path = fisher_config.get_model_path()
            if not Path(model_path).exists():
                print(f"模型文件不存在: {model_path}")
                return False
            
            # 设置计算设备
            self.device = self._get_device()
            print(f"使用计算设备: {self.device}")
            
            # 加载模型（禁用详细日志）
            self.model = YOLO(model_path, verbose=False)
            self.model.to(self.device)
            
            print(f"模型加载成功: {model_path}")
            self.is_initialized = True
            return True
            
        except Exception as e:
            print(f"模型初始化失败: {e}")
            self.is_initialized = False
            return False
    
    def _get_device(self) -> str:
        """
        获取最佳计算设备
        
        Returns:
            str: 设备类型 (cuda/cpu)
        """
        config_device = fisher_config.model.device.lower()
        
        if config_device == "auto":
            # 自动选择设备
            if torch.cuda.is_available():
                return "cuda"
            else:
                return "cpu"
        elif config_device == "cuda":
            if torch.cuda.is_available():
                return "cuda"
            else:
                print("CUDA不可用，使用CPU")
                return "cpu"
        else:
            return "cpu"
    
    def capture_screen(self, region: Optional[Tuple[int, int, int, int]] = None) -> Optional[np.ndarray]:
        """
        截取屏幕图像
        
        Args:
            region: 截取区域 (left, top, width, height)，None表示全屏
            
        Returns:
            np.ndarray: 截取的图像，BGR格式
        """
        try:
            # 线程安全的screenshot工具初始化
            if self.screenshot_tool is None:
                self.screenshot_tool = mss.mss()
            
            if region:
                # 指定区域截图
                monitor = {
                    "left": region[0],
                    "top": region[1], 
                    "width": region[2],
                    "height": region[3]
                }
            else:
                # 全屏截图
                monitor = self.screenshot_tool.monitors[1]  # 主显示器
            
            # 截取屏幕
            screenshot = self.screenshot_tool.grab(monitor)
            
            # 转换为numpy数组
            img = np.array(screenshot)
            
            # 转换颜色格式：BGRA -> BGR
            if img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            elif img.shape[2] == 3:
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            
            return img
            
        except Exception as e:
            print(f"屏幕截取失败: {e}")
            return None
    
    def detect_states(self, image: Optional[np.ndarray] = None, 
                     region: Optional[Tuple[int, int, int, int]] = None) -> Optional[Dict]:
        """
        检测钓鱼状态
        
        Args:
            image: 输入图像，如果为None则自动截屏
            region: 截屏区域，仅在image为None时有效
            
        Returns:
            Dict: 检测结果 {
                'state': int,           # 检测到的状态编号
                'confidence': float,    # 置信度
                'state_name': str,      # 状态名称
                'bbox': List[float]     # 边界框坐标 [x1, y1, x2, y2]
            }
        """
        if not self.is_initialized:
            print("模型未初始化")
            return None
        
        try:
            # 获取图像
            if image is None:
                image = self.capture_screen(region)
                if image is None:
                    return None
            
            # 模型推理（禁用详细日志输出）
            results = self.model(image, conf=fisher_config.model.confidence_threshold, verbose=False)
            
            # 解析结果
            if len(results) > 0 and len(results[0].boxes) > 0:
                # 获取置信度最高的检测结果
                boxes = results[0].boxes
                confidences = boxes.conf.cpu().numpy()
                classes = boxes.cls.cpu().numpy().astype(int)
                bboxes = boxes.xyxy.cpu().numpy()
                
                # 找到置信度最高的结果
                max_conf_idx = np.argmax(confidences)
                best_class = classes[max_conf_idx]
                best_conf = confidences[max_conf_idx]
                best_bbox = bboxes[max_conf_idx].tolist()
                
                # 构造返回结果
                result = {
                    'state': best_class,
                    'confidence': float(best_conf),
                    'state_name': self.state_names.get(best_class, f"未知状态_{best_class}"),
                    'bbox': best_bbox
                }
                
                return result
            
            return None
            
        except Exception as e:
            print(f"状态检测失败: {e}")
            return None
    
    def detect_specific_state(self, target_state: int, 
                            image: Optional[np.ndarray] = None,
                            region: Optional[Tuple[int, int, int, int]] = None) -> bool:
        """
        检测特定状态是否存在
        
        Args:
            target_state: 目标状态编号
            image: 输入图像，如果为None则自动截屏
            region: 截屏区域，仅在image为None时有效
            
        Returns:
            bool: 是否检测到目标状态
        """
        result = self.detect_states(image, region)
        if result:
            return result['state'] == target_state
        return False
    
    def detect_multiple_states(self, target_states: List[int],
                             image: Optional[np.ndarray] = None,
                             region: Optional[Tuple[int, int, int, int]] = None) -> Optional[Dict]:
        """
        检测多个目标状态中的任意一个
        
        Args:
            target_states: 目标状态列表
            image: 输入图像，如果为None则自动截屏  
            region: 截屏区域，仅在image为None时有效
            
        Returns:
            Dict: 检测结果，如果检测到目标状态之一
        """
        result = self.detect_states(image, region)
        if result and result['state'] in target_states:
            return result
        return None
    
    def get_detection_info(self) -> Dict:
        """
        获取检测器信息
        
        Returns:
            Dict: 检测器信息
        """
        return {
            'initialized': self.is_initialized,
            'device': self.device,
            'model_path': fisher_config.get_model_path() if self.is_initialized else None,
            'confidence_threshold': fisher_config.model.confidence_threshold,
            'state_names': self.state_names
        }
    
    def reload_model(self) -> bool:
        """
        重新加载模型
        
        Returns:
            bool: 重新加载是否成功
        """
        print("正在重新加载模型...")
        self.is_initialized = False
        return self._initialize_model()
    
    def cleanup(self) -> None:
        """清理资源"""
        try:
            if self.model:
                del self.model
            if self.screenshot_tool:
                self.screenshot_tool.close()
                self.screenshot_tool = None
            print("模型检测器资源清理完成")
        except Exception as e:
            print(f"资源清理失败: {e}")

# 全局模型检测器实例
model_detector = ModelDetector() 