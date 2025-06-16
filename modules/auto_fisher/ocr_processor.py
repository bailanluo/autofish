#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
OCR处理器模块

该模块负责使用Tesseract OCR识别游戏中的文字，特别是"向左拉"和"向右拉"的提示。
"""

import os
import time
import logging
import threading
import numpy as np
import cv2
import pytesseract
from typing import Optional, Dict, List, Tuple

# 导入相关模块
from modules.auto_fisher.config_manager import get_instance as get_config_manager


class OCRProcessor:
    """
    OCR处理器类
    
    负责识别游戏中的文字提示，特别是"向左拉"和"向右拉"的提示。
    """
    
    def __init__(self):
        """
        初始化OCR处理器
        """
        # 获取配置管理器
        self.config_manager = get_config_manager()
        
        # 获取OCR配置
        self.ocr_config = self.config_manager.get_config('ocr')
        
        # 设置Tesseract路径
        tesseract_path = self.ocr_config.get('tesseract_path', "D:\\Python\\tool\\Tesseract-OCR\\tesseract.exe")
        if os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            logging.info(f"已设置Tesseract路径: {tesseract_path}")
        else:
            logging.warning(f"Tesseract路径不存在: {tesseract_path}")
        
        # OCR配置
        self.tesseract_config = self.ocr_config.get('config', '--psm 7 --oem 1') + ' -l ' + self.ocr_config.get('language', 'chi_sim')
        
        # 文字识别区域
        self.roi = None
        
        # 识别结果缓存
        self.last_result = None
        self.last_result_time = 0
        self.result_cache_time = 0.2  # 结果缓存时间（秒）
        
        # OCR线程
        self.ocr_thread = None
        self.is_running = False
        self.is_paused = False
        self.ocr_lock = threading.Lock()
        
        # 识别关键词
        self.keywords = self.ocr_config.get('keywords', {
            "left": ["向左拉", "左拉", "向左", "拉左"],
            "right": ["向右拉", "右拉", "向右", "拉右"]
        })
        
        # 回调函数
        self.direction_callback = None
        
        logging.info("OCR处理器初始化完成")
    
    def set_roi(self, x: int, y: int, width: int, height: int):
        """
        设置OCR识别区域
        
        Args:
            x: 左上角x坐标
            y: 左上角y坐标
            width: 宽度
            height: 高度
        """
        self.roi = (x, y, width, height)
        logging.info(f"OCR识别区域已设置: x={x}, y={y}, width={width}, height={height}")
    
    def set_direction_callback(self, callback):
        """
        设置方向识别回调函数
        
        Args:
            callback: 回调函数，接收方向参数('left'或'right')
        """
        self.direction_callback = callback
        logging.info("OCR方向回调函数已设置")
    
    def start(self):
        """
        启动OCR识别线程
        """
        if self.is_running:
            logging.warning("OCR处理器已在运行中")
            return
        
        # 检查是否启用OCR
        if not self.ocr_config.get('enabled', True):
            logging.info("OCR功能已在配置中禁用，不启动OCR处理器")
            return
        
        self.is_running = True
        self.is_paused = False
        
        # 启动OCR线程
        self.ocr_thread = threading.Thread(target=self._ocr_loop, daemon=True)
        self.ocr_thread.start()
        
        logging.info("OCR处理器已启动")
    
    def stop(self):
        """
        停止OCR识别线程
        """
        if not self.is_running:
            return
        
        self.is_running = False
        
        # 等待线程结束（最多等待3秒）
        if self.ocr_thread and self.ocr_thread.is_alive():
            self.ocr_thread.join(timeout=3)
        
        logging.info("OCR处理器已停止")
    
    def pause(self):
        """
        暂停OCR识别
        """
        if self.is_running and not self.is_paused:
            self.is_paused = True
            logging.info("OCR处理器已暂停")
    
    def resume(self):
        """
        恢复OCR识别
        """
        if self.is_running and self.is_paused:
            self.is_paused = False
            logging.info("OCR处理器已恢复")
    
    def _ocr_loop(self):
        """
        OCR识别循环
        """
        try:
            while self.is_running:
                # 如果暂停，则等待
                if self.is_paused:
                    time.sleep(0.1)
                    continue
                
                # 执行OCR识别
                self._perform_ocr()
                
                # 短暂休眠以降低CPU占用
                time.sleep(0.1)
                
        except Exception as e:
            logging.error(f"OCR处理器运行出错: {str(e)}")
            self.stop()
    
    def _perform_ocr(self):
        """
        执行OCR识别
        """
        try:
            # 检查是否设置了ROI
            if not self.roi:
                logging.warning("OCR识别区域(ROI)未设置，无法进行文字识别")
                return
            
            # 截取屏幕区域
            import mss
            with mss.mss() as sct:
                monitor = {"left": self.roi[0], "top": self.roi[1], 
                          "width": self.roi[2], "height": self.roi[3]}
                screenshot = np.array(sct.grab(monitor))
            
            logging.debug(f"OCR截取屏幕区域: x={self.roi[0]}, y={self.roi[1]}, width={self.roi[2]}, height={self.roi[3]}")
            
            # 转换为灰度图
            gray = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2GRAY)
            
            # 图像预处理
            _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
            
            # 执行OCR识别
            logging.debug(f"执行OCR识别，使用配置: {self.tesseract_config}")
            text = pytesseract.image_to_string(binary, config=self.tesseract_config)
            text = text.strip().lower()
            
            logging.debug(f"OCR原始识别结果: '{text}'")
            
            # 检查是否包含关键词
            direction = self._check_direction(text)
            
            # 如果识别到方向，调用回调函数
            if direction:
                logging.info(f"OCR识别到方向: {direction}，原始文本: '{text}'")
                if self.direction_callback:
                    self.direction_callback(direction)
                else:
                    logging.warning("OCR方向回调函数未设置，无法处理识别结果")
            
            # 更新缓存
            with self.ocr_lock:
                self.last_result = text
                self.last_result_time = time.time()
            
        except Exception as e:
            logging.error(f"OCR识别失败: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
    
    def _check_direction(self, text: str) -> Optional[str]:
        """
        检查文本中是否包含方向关键词
        
        Args:
            text: 识别的文本
        
        Returns:
            方向('left', 'right')或None
        """
        # 检查左拉关键词
        for keyword in self.keywords["left"]:
            if keyword in text:
                return "left"
        
        # 检查右拉关键词
        for keyword in self.keywords["right"]:
            if keyword in text:
                return "right"
        
        return None
    
    def get_last_result(self) -> Tuple[Optional[str], float]:
        """
        获取最近一次的OCR识别结果
        
        Returns:
            (识别文本, 识别时间戳)的元组
        """
        with self.ocr_lock:
            return self.last_result, self.last_result_time


# 单例模式
_instance = None

def get_instance():
    """
    获取OCR处理器单例
    
    Returns:
        OCRProcessor实例
    """
    global _instance
    if _instance is None:
        _instance = OCRProcessor()
    return _instance 