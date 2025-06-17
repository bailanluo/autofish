#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AutoFish钓鱼状态检测器模块

统一的状态检测器，集成YOLO模型检测和OCR文字识别功能。
"""

import cv2
import time
import logging
import numpy as np
import mss
import pytesseract
import threading
from typing import Dict, Optional, Tuple, List
from ultralytics import YOLO
from PIL import Image, ImageEnhance
import os

from modules.auto_fisher.config import get_config


class StateDetector:
    """状态检测器类"""
    
    def __init__(self):
        """初始化状态检测器"""
        self.config = get_config()
        
        # 初始化YOLO模型
        self.model = None
        self.load_model()
        
        # 初始化OCR
        self.init_ocr()
        
        # 线程本地存储，为每个线程创建独立的mss实例
        self._local = threading.local()
        
        # 检测区域（可配置）
        self.detection_region = None
        
        # 状态映射
        self.state_names = {
            0: "等待上钩状态",
            1: "鱼上钩末提线状态",
            2: "提线中_耐力未到二分之一状态", 
            3: "提线中_耐力已到二分之一状态",
            4: "向右拉_txt",
            5: "向左拉_txt",
            6: "钓鱼成功状态_txt"
        }
        
        logging.info("状态检测器初始化完成")
    
    def load_model(self):
        """加载YOLO模型"""
        try:
            model_path = self.config.get_model_path()
            if os.path.exists(model_path):
                self.model = YOLO(model_path)
                logging.info(f"YOLO模型加载成功: {model_path}")
            else:
                logging.error(f"模型文件不存在: {model_path}")
                raise FileNotFoundError(f"模型文件不存在: {model_path}")
        except Exception as e:
            logging.error(f"加载YOLO模型失败: {e}")
            raise
    
    def init_ocr(self):
        """初始化OCR"""
        try:
            tesseract_path = self.config.get_tesseract_path()
            if os.path.exists(tesseract_path):
                pytesseract.pytesseract.tesseract_cmd = os.path.join(tesseract_path, 'tesseract.exe')
                logging.info(f"Tesseract OCR初始化成功: {tesseract_path}")
            else:
                logging.error(f"Tesseract路径不存在: {tesseract_path}")
        except Exception as e:
            logging.error(f"初始化OCR失败: {e}")
    
    def _get_sct(self):
        """获取线程本地的mss实例"""
        if not hasattr(self._local, 'sct'):
            self._local.sct = mss.mss()
        return self._local.sct
    
    def capture_screen(self) -> Optional[np.ndarray]:
        """捕获屏幕截图"""
        try:
            # 获取线程本地的mss实例
            sct = self._get_sct()
            
            if self.detection_region:
                # 使用指定区域
                screenshot = sct.grab(self.detection_region)
            else:
                # 使用全屏
                screenshot = sct.grab(sct.monitors[1])
            
            # 转换为numpy数组
            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
            return img
        except Exception as e:
            logging.error(f"捕获屏幕失败: {e}")
            return None
    
    def detect_yolo_states(self, image: np.ndarray) -> Dict[int, float]:
        """
        使用YOLO模型检测状态
        
        Args:
            image: 输入图像
            
        Returns:
            Dict[int, float]: 状态ID -> 置信度
        """
        if self.model is None:
            return {}
        
        try:
            # 进行预测
            results = self.model(image, verbose=False)
            
            # 解析结果
            detections = {}
            confidence_threshold = self.config.get('model.confidence_threshold', 0.5)
            
            for result in results:
                if result.boxes is not None:
                    for box in result.boxes:
                        class_id = int(box.cls.cpu().numpy()[0])
                        confidence = float(box.conf.cpu().numpy()[0])
                        
                        # 只保留置信度高于阈值的检测
                        if confidence >= confidence_threshold:
                            if class_id not in detections or confidence > detections[class_id]:
                                detections[class_id] = confidence
            
            return detections
        except Exception as e:
            logging.error(f"YOLO检测失败: {e}")
            return {}
    
    def detect_ocr_states(self, image: np.ndarray) -> Dict[int, float]:
        """
        使用OCR检测文字状态
        
        Args:
            image: 输入图像
            
        Returns:
            Dict[int, float]: 状态ID -> 置信度
        """
        try:
            # 转换为PIL图像
            pil_image = Image.fromarray(image)
            
            # 图像预处理
            pil_image = self.preprocess_image_for_ocr(pil_image)
            
            # 进行OCR识别
            lang = self.config.get('ocr.language', 'chi_sim+eng')
            text = pytesseract.image_to_string(pil_image, lang=lang)
            
            # 文字状态检测
            detections = {}
            confidence_threshold = self.config.get('ocr.confidence_threshold', 60)
            
            # 检测向右拉和向左拉
            if "向右拉" in text or "右拉" in text:
                detections[4] = 0.8  # 向右拉状态
            if "向左拉" in text or "左拉" in text:
                detections[5] = 0.8  # 向左拉状态
            if "钓鱼成功" in text or "成功" in text:
                detections[6] = 0.8  # 钓鱼成功状态
            
            return detections
        except Exception as e:
            logging.error(f"OCR检测失败: {e}")
            return {}
    
    def preprocess_image_for_ocr(self, image: Image.Image) -> Image.Image:
        """
        OCR图像预处理
        
        Args:
            image: 输入图像
            
        Returns:
            预处理后的图像
        """
        try:
            # 放大图像
            image = image.resize((image.width * 2, image.height * 2), Image.LANCZOS)
            
            # 转换为灰度图
            image = image.convert('L')
            
            # 增强对比度
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # 二值化
            image = image.point(lambda x: 0 if x < 128 else 255, '1')
            
            return image
        except Exception as e:
            logging.error(f"OCR图像预处理失败: {e}")
            return image
    
    def detect_states(self) -> Dict[int, float]:
        """
        检测所有状态
        
        Returns:
            Dict[int, float]: 状态ID -> 置信度
        """
        # 捕获屏幕
        image = self.capture_screen()
        if image is None:
            return {}
        
        # YOLO检测
        yolo_detections = self.detect_yolo_states(image)
        
        # OCR检测
        ocr_detections = self.detect_ocr_states(image)
        
        # 合并检测结果
        all_detections = {}
        all_detections.update(yolo_detections)
        all_detections.update(ocr_detections)
        
        return all_detections
    
    def get_highest_confidence_state(self, detections: Dict[int, float]) -> Optional[Tuple[int, float]]:
        """
        获取置信度最高的状态
        
        Args:
            detections: 检测结果
            
        Returns:
            (状态ID, 置信度) 或 None
        """
        if not detections:
            return None
        
        # 找到置信度最高的状态
        best_state = max(detections.items(), key=lambda x: x[1])
        return best_state
    
    def set_detection_region(self, region: Optional[Dict[str, int]]):
        """
        设置检测区域
        
        Args:
            region: 检测区域字典 {'top': y, 'left': x, 'width': w, 'height': h}
        """
        self.detection_region = region
        if region:
            logging.info(f"设置检测区域: {region}")
        else:
            logging.info("取消检测区域限制")
    
    def get_state_name(self, state_id: int) -> str:
        """获取状态名称"""
        return self.state_names.get(state_id, f"未知状态{state_id}")


# 全局检测器实例
_detector_instance: Optional[StateDetector] = None


def get_detector() -> StateDetector:
    """获取状态检测器实例"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = StateDetector()
    return _detector_instance 