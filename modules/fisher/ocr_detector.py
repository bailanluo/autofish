"""
Fisher钓鱼模块OCR检测器
负责识别状态4和5的文字内容："向左拉"和"向右拉"

作者: AutoFish Team
版本: v1.0
创建时间: 2024-12-28
"""

import cv2
import numpy as np
import pytesseract
import os
from typing import Optional, Dict, List, Tuple
from pathlib import Path
import mss

from .config import fisher_config


class OCRDetector:
    """OCR文字检测器"""
    
    def __init__(self):
        """
        初始化OCR检测器
        """
        self.is_initialized: bool = False  # 初始化状态
        self.screenshot_tool = None  # 屏幕截图工具（延迟初始化）
        
        # 目标文字列表
        self.target_texts = {
            4: ["向右拉", "向右", "右拉"],  # 状态4可能的文字
            5: ["向左拉", "向左", "左拉"]   # 状态5可能的文字
        }
        
        # 初始化OCR
        self._initialize_ocr()
    
    def _initialize_ocr(self) -> bool:
        """
        初始化Tesseract OCR
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 设置Tesseract路径
            tesseract_path = fisher_config.ocr.tesseract_path
            tesseract_exe = os.path.join(tesseract_path, "tesseract.exe")
            
            if not os.path.exists(tesseract_exe):
                print(f"Tesseract执行文件不存在: {tesseract_exe}")
                return False
            
            # 设置Tesseract路径
            pytesseract.pytesseract.tesseract_cmd = tesseract_exe
            
            # 测试OCR是否可用
            test_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
            cv2.putText(test_image, "TEST", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
            
            # 尝试识别测试图像
            result = pytesseract.image_to_string(test_image, lang=fisher_config.ocr.language)
            
            print(f"OCR初始化成功，测试结果: {result.strip()}")
            self.is_initialized = True
            return True
            
        except Exception as e:
            print(f"OCR初始化失败: {e}")
            self.is_initialized = False
            return False
    
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
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        图像预处理，提高OCR识别准确率
        
        Args:
            image: 输入图像
            
        Returns:
            np.ndarray: 预处理后的图像
        """
        try:
            # 转换为灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # 图像缩放，提高OCR准确率
            height, width = gray.shape
            scale_factor = max(2, 200 // min(height, width))  # 最小缩放到200像素
            new_width = width * scale_factor
            new_height = height * scale_factor
            gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            # 高斯模糊去噪
            gray = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # 自适应阈值二值化
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # 形态学操作，去除噪点
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            return binary
            
        except Exception as e:
            print(f"图像预处理失败: {e}")
            return image
    
    def extract_text(self, image: np.ndarray, preprocess: bool = True) -> str:
        """
        从图像中提取文字
        
        Args:
            image: 输入图像
            preprocess: 是否进行预处理
            
        Returns:
            str: 识别到的文字
        """
        if not self.is_initialized:
            print("OCR未初始化")
            return ""
        
        try:
            # 图像预处理
            if preprocess:
                processed_image = self.preprocess_image(image)
            else:
                processed_image = image
            
            # OCR识别配置
            config = f'--oem 3 --psm 6 -c tessedit_char_whitelist=向左右拉'
            
            # 提取文字
            text = pytesseract.image_to_string(
                processed_image, 
                lang=fisher_config.ocr.language,
                config=config
            )
            
            # 清理文字
            text = text.strip().replace('\n', '').replace(' ', '')
            
            return text
            
        except Exception as e:
            print(f"文字提取失败: {e}")
            return ""
    
    def extract_text_with_confidence(self, image: np.ndarray, preprocess: bool = True) -> List[Dict]:
        """
        从图像中提取文字和置信度
        
        Args:
            image: 输入图像
            preprocess: 是否进行预处理
            
        Returns:
            List[Dict]: 识别结果列表，每个元素包含文字和置信度
        """
        if not self.is_initialized:
            print("OCR未初始化")
            return []
        
        try:
            # 图像预处理
            if preprocess:
                processed_image = self.preprocess_image(image)
            else:
                processed_image = image
            
            # OCR识别配置
            config = f'--oem 3 --psm 6 -c tessedit_char_whitelist=向左右拉'
            
            # 获取详细信息
            data = pytesseract.image_to_data(
                processed_image,
                lang=fisher_config.ocr.language,
                config=config,
                output_type=pytesseract.Output.DICT
            )
            
            results = []
            for i, text in enumerate(data['text']):
                if text.strip():
                    confidence = int(data['conf'][i])
                    if confidence >= fisher_config.ocr.confidence_threshold:
                        results.append({
                            'text': text.strip(),
                            'confidence': confidence,
                            'bbox': [data['left'][i], data['top'][i], 
                                   data['width'][i], data['height'][i]]
                        })
            
            return results
            
        except Exception as e:
            print(f"文字提取失败: {e}")
            return []
    
    def detect_direction_text(self, image: Optional[np.ndarray] = None,
                            region: Optional[Tuple[int, int, int, int]] = None) -> Optional[int]:
        """
        检测方向文字（状态4或5）
        
        Args:
            image: 输入图像，如果为None则自动截屏
            region: 截屏区域，仅在image为None时有效
            
        Returns:
            int: 检测到的状态编号（4或5），如果未检测到则返回None
        """
        if not self.is_initialized:
            print("OCR未初始化")
            return None
        
        try:
            # 获取图像
            if image is None:
                image = self.capture_screen(region)
                if image is None:
                    return None
            
            # 提取文字
            text = self.extract_text(image)
            
            # 检查是否包含目标文字
            for state, target_list in self.target_texts.items():
                for target in target_list:
                    if target in text:
                        return state
            
            return None
            
        except Exception as e:
            print(f"方向文字检测失败: {e}")
            return None
    
    def detect_direction_text_with_confidence(self, image: Optional[np.ndarray] = None,
                                            region: Optional[Tuple[int, int, int, int]] = None) -> Optional[Dict]:
        """
        检测方向文字（状态4或5）并返回置信度
        
        Args:
            image: 输入图像，如果为None则自动截屏
            region: 截屏区域，仅在image为None时有效
            
        Returns:
            Dict: 检测结果 {
                'state': int,           # 状态编号
                'text': str,            # 识别到的文字
                'confidence': int,      # 置信度
                'bbox': List[int]       # 边界框
            }
        """
        if not self.is_initialized:
            print("OCR未初始化")
            return None
        
        try:
            # 获取图像
            if image is None:
                image = self.capture_screen(region)
                if image is None:
                    return None
            
            # 提取文字和置信度
            results = self.extract_text_with_confidence(image)
            
            # 检查是否包含目标文字
            for result in results:
                text = result['text']
                for state, target_list in self.target_texts.items():
                    for target in target_list:
                        if target in text:
                            return {
                                'state': state,
                                'text': text,
                                'confidence': result['confidence'],
                                'bbox': result['bbox']
                            }
            
            return None
            
        except Exception as e:
            print(f"方向文字检测失败: {e}")
            return None
    
    def get_ocr_info(self) -> Dict:
        """
        获取OCR检测器信息
        
        Returns:
            Dict: OCR检测器信息
        """
        return {
            'initialized': self.is_initialized,
            'tesseract_path': fisher_config.ocr.tesseract_path,
            'language': fisher_config.ocr.language,
            'confidence_threshold': fisher_config.ocr.confidence_threshold,
            'target_texts': self.target_texts
        }
    
    def cleanup(self) -> None:
        """清理资源"""
        try:
            if self.screenshot_tool:
                self.screenshot_tool.close()
                self.screenshot_tool = None
            print("OCR检测器资源清理完成")
        except Exception as e:
            print(f"资源清理失败: {e}")

# 全局OCR检测器实例
ocr_detector = OCRDetector() 