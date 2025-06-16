#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
模型检测器模块

该模块负责加载YOLO模型，并对屏幕截图进行分析以检测当前游戏状态。
"""

import os
import time
import logging
import numpy as np
from pathlib import Path
import torch
from ultralytics import YOLO
import cv2
import mss
from typing import Dict, List, Tuple, Optional
import threading

# 导入配置管理器
from modules.auto_fisher.config_manager import get_instance as get_config_manager


class ModelDetector:
    """
    模型检测器类
    
    负责使用YOLO模型检测游戏中的各种状态。
    """
    
    def __init__(self):
        """
        初始化模型检测器
        """
        # 获取配置管理器
        self.config_manager = get_config_manager()
        
        # 模型路径
        self.model_path = self.config_manager.get_model_path()
        
        # 检测置信度阈值
        self.confidence = self.config_manager.get_model_confidence()
        
        # 类别映射
        self.class_mapping = self.config_manager.get_class_mapping()
        
        # 打印类别映射表，用于调试
        self._print_class_mapping()
        
        # 检查模型文件是否存在
        if not os.path.exists(self.model_path):
            logging.error(f"模型文件不存在: {self.model_path}")
            raise FileNotFoundError(f"找不到模型文件: {self.model_path}")
        
        # 初始化模型
        self.model = self._load_model()
        
        # 屏幕捕获工具 - 为每个线程创建单独的实例
        self.sct = None
        
        # 屏幕区域（默认为全屏）
        self.monitor = None  # 在捕获时确定
        
        # 截图锁，防止多线程同时截图
        self.capture_lock = threading.Lock()
        
        logging.info(f"模型检测器初始化完成，使用模型: {self.model_path}")
    
    def _print_class_mapping(self):
        """
        打印类别映射表，用于调试
        """
        logging.info("类别映射表:")
        for class_id, class_name in self.class_mapping.items():
            try:
                # 检查编码
                encoded_name = class_name.encode('utf-8').decode('utf-8')
                logging.info(f"  类别ID: {class_id} -> 名称: '{encoded_name}' (编码正常)")
            except UnicodeError:
                logging.error(f"  类别ID: {class_id} -> 名称编码错误")
                
        # 检查模型可能使用的类别范围
        max_id = max(self.class_mapping.keys()) if self.class_mapping else -1
        logging.info(f"类别ID范围: 0-{max_id}")
        
        # 检查是否有缺失的类别ID
        missing_ids = []
        for i in range(max_id + 1):
            if i not in self.class_mapping:
                missing_ids.append(i)
        
        if missing_ids:
            logging.warning(f"缺失的类别ID: {missing_ids}")
        else:
            logging.info("类别映射表完整，无缺失ID")
    
    def _load_model(self) -> YOLO:
        """
        加载YOLO模型
        
        Returns:
            加载的YOLO模型实例
        """
        try:
            # 设置设备 (GPU或CPU)
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            logging.info(f"使用设备: {device} 加载模型")
            
            # 加载模型
            model = YOLO(self.model_path)
            model.to(device)
            
            # 预热模型
            dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
            model(dummy_img, verbose=False)
            
            # 检查模型类别数量
            try:
                # 获取模型的类别数量
                num_classes = model.names
                logging.info(f"模型类别数量: {len(num_classes)}")
                logging.info(f"模型类别映射: {model.names}")
                
                # 创建新的类别映射，使用模型自身的类别名称，但保留配置文件中的中文显示名称
                config_mapping = self.class_mapping.copy()  # 保存原始配置映射
                new_mapping = {}
                
                # 遍历模型中的所有类别
                for i, name in enumerate(model.names):
                    if i in config_mapping:
                        # 使用配置中的中文名称
                        new_mapping[i] = config_mapping[i]
                        logging.info(f"类别ID {i}: 使用配置名称 '{config_mapping[i]}'")
                    else:
                        # 对于模型中存在但配置中不存在的类别，使用默认名称
                        new_mapping[i] = f"类别{i}"
                        logging.info(f"类别ID {i}: 使用默认名称 '类别{i}'")
                
                # 更新类别映射
                self.class_mapping = new_mapping
                logging.info(f"更新后的类别映射: {self.class_mapping}")
                
                # 检查是否有配置中存在但模型中不存在的类别
                for i in config_mapping:
                    if i >= len(model.names):
                        logging.warning(f"配置中的类别ID {i} 在模型中不存在")
                
            except Exception as e:
                logging.error(f"处理模型类别时出错: {str(e)}")
                import traceback
                logging.error(traceback.format_exc())
            
            logging.info("YOLO模型加载成功")
            return model
            
        except Exception as e:
            logging.error(f"加载模型失败: {str(e)}")
            raise RuntimeError(f"无法加载YOLO模型: {str(e)}")
    
    def set_monitor_area(self, left: int, top: int, width: int, height: int):
        """
        设置检测的屏幕区域
        
        Args:
            left: 左边距离
            top: 顶部距离
            width: 宽度
            height: 高度
        """
        self.monitor = {"left": left, "top": top, "width": width, "height": height}
        logging.info(f"已设置检测区域: {self.monitor}")
    
    def capture_screen(self) -> np.ndarray:
        """
        捕获屏幕截图 - 线程安全
        
        Returns:
            屏幕截图的numpy数组，格式为BGR
        """
        with self.capture_lock:
            try:
                # 每次捕获时创建新的MSS实例，解决线程问题
                with mss.mss() as sct:
                    # 如果未设置monitor，使用默认值
                    if self.monitor is None:
                        self.monitor = sct.monitors[0]  # 主显示器
                    
                    # 获取屏幕截图
                    screenshot = np.array(sct.grab(self.monitor))
                    # 转换BGRA为BGR
                    return cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
                    
            except Exception as e:
                logging.error(f"屏幕捕获失败: {str(e)}")
                # 返回空图像而不是抛出异常
                return np.zeros((100, 100, 3), dtype=np.uint8)
    
    def detect(self) -> Tuple[List[int], List[float]]:
        """
        检测当前屏幕状态
        
        Returns:
            检测到的类别ID列表和对应的置信度列表
        """
        try:
            # 捕获屏幕
            img = self.capture_screen()
            
            # 记录图像尺寸
            h, w, _ = img.shape
            logging.debug(f"截图尺寸: {w}x{h}")
            
            if h <= 1 or w <= 1:
                logging.error(f"截图异常: 尺寸过小 {w}x{h}")
                return [], []
            
            # 执行检测
            results = self.model(img, verbose=False, conf=self.confidence)[0]
            
            # 记录原始检测结果
            logging.debug(f"原始检测结果: {results}")
            
            # 是否需要显示检测结果
            if self.config_manager.get_display_config().get('show_detection', False):
                self._show_detection_results(img, results)
            
            # 提取检测到的类别和置信度
            detected_classes = []
            detected_confidences = []
            
            # 记录原始检测结果
            num_detections = len(results.boxes)
            logging.info(f"检测到 {num_detections} 个目标")
            
            if num_detections > 0:
                # 记录所有类别的原始信息
                all_classes = results.boxes.cls.tolist()
                all_confs = results.boxes.conf.tolist()
                logging.debug(f"检测到的所有类别ID: {all_classes}")
                logging.debug(f"检测到的所有置信度: {all_confs}")
            
            for r in results.boxes.data.tolist():
                x1, y1, x2, y2, conf, cls = r
                class_id = int(cls)
                detected_classes.append(class_id)
                detected_confidences.append(conf)
                
                # 详细记录每个检测结果
                class_name = self.get_state_name(class_id)
                logging.info(f"检测到: {class_name} (ID: {class_id}) - 置信度: {conf:.2f}, 位置: [{int(x1)}, {int(y1)}, {int(x2)}, {int(y2)}]")
            
            return detected_classes, detected_confidences
        
        except Exception as e:
            logging.error(f"检测过程出错: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            return [], []
    
    def _show_detection_results(self, img: np.ndarray, results) -> None:
        """
        显示检测结果
        
        Args:
            img: 原始图像
            results: 检测结果
        """
        try:
            # 创建图像副本用于绘制
            img_draw = img.copy()
            
            # 绘制检测框
            for r in results.boxes.data.tolist():
                x1, y1, x2, y2, conf, cls = r
                class_id = int(cls)
                class_name = self.get_state_name(class_id)
                
                # 画框
                cv2.rectangle(img_draw, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                
                # 添加标签 - 使用简单的标签格式
                # OpenCV不能很好地显示中文，所以只显示ID和置信度
                label = f"ID:{class_id} {conf:.2f}"
                cv2.putText(img_draw, label, (int(x1), int(y1) - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # 在图像顶部添加检测到的状态信息
            detected_info = []
            for r in results.boxes.data.tolist():
                _, _, _, _, conf, cls = r
                class_id = int(cls)
                class_name = self.get_state_name(class_id)
                detected_info.append(f"{class_name}({conf:.2f})")
            
            # 在图像顶部添加状态信息
            status_text = " | ".join(detected_info)
            cv2.putText(img_draw, status_text, (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            # 缩小图像以便显示
            scale = 0.5
            img_resized = cv2.resize(img_draw, (0, 0), fx=scale, fy=scale)
            
            # 显示图像
            cv2.imshow('AutoFish Detection', img_resized)
            cv2.waitKey(1)  # 显示1毫秒
            
        except Exception as e:
            logging.error(f"显示检测结果出错: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            # 如果出错，尝试关闭窗口
            try:
                cv2.destroyWindow('AutoFish Detection')
            except:
                pass
    
    def get_current_state(self) -> Dict[int, float]:
        """
        获取当前状态，返回所有检测到的类别及其置信度
        
        Returns:
            包含类别ID和置信度的字典
        """
        classes, confidences = self.detect()
        return {cls: conf for cls, conf in zip(classes, confidences)}
    
    def is_state_detected(self, state_id: int) -> Tuple[bool, float]:
        """
        检查特定状态是否被检测到
        
        Args:
            state_id: 要检查的状态ID
        
        Returns:
            (是否检测到, 置信度) 的元组
        """
        state_dict = self.get_current_state()
        if state_id in state_dict:
            return True, state_dict[state_id]
        return False, 0.0
    
    def get_state_name(self, state_id: int) -> str:
        """
        获取状态ID对应的名称
        
        Args:
            state_id: 状态ID
            
        Returns:
            状态名称
        """
        if state_id in self.class_mapping:
            return self.class_mapping[state_id]
        return f"未知状态({state_id})"
    
    def get_highest_confidence_state(self) -> Optional[Tuple[int, float]]:
        """
        获取置信度最高的状态
        
        Returns:
            (状态ID, 置信度) 的元组，如果没有检测到任何状态则返回None
        """
        state_dict = self.get_current_state()
        if not state_dict:
            return None
        
        # 找出置信度最高的状态
        max_state = max(state_dict.items(), key=lambda x: x[1])
        return max_state


# 单例模式
_instance = None

def get_instance():
    """
    获取模型检测器单例
    
    Returns:
        ModelDetector实例
    """
    global _instance
    if _instance is None:
        _instance = ModelDetector()
    return _instance 