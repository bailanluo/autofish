#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
按键控制器模块

该模块负责处理OCR识别到的方向指令，实现长按A键或D键的功能。
"""

import time
import logging
import threading
import pyautogui
from typing import Optional

# 导入相关模块
from modules.auto_fisher.config_manager import get_instance as get_config_manager


class KeyController:
    """
    按键控制器类
    
    负责处理OCR识别到的方向指令，实现长按A键或D键的功能。
    """
    
    def __init__(self):
        """
        初始化按键控制器
        """
        # 获取配置管理器
        self.config_manager = get_config_manager()
        
        # 获取OCR配置
        self.ocr_config = self.config_manager.get_config('ocr')
        
        # 当前按下的按键
        self.current_key = None
        
        # 按键状态
        self.key_pressed = False
        
        # 按键持续时间（秒）
        self.key_duration = self.ocr_config.get('key_duration', 1.0)
        
        # 按键线程
        self.key_thread = None
        self.is_running = False
        self.stop_flag = threading.Event()
        
        logging.info(f"按键控制器初始化完成，按键持续时间: {self.key_duration}秒")
    
    def handle_direction(self, direction: str):
        """
        处理方向指令
        
        Args:
            direction: 方向('left'或'right')
        """
        if direction == "left":
            self.press_key('a')
        elif direction == "right":
            self.press_key('d')
    
    def press_key(self, key: str):
        """
        长按指定按键
        
        Args:
            key: 要按下的按键
        """
        # 如果当前已经在按下同一个按键，则不重复操作
        if self.current_key == key and self.key_pressed:
            return
        
        # 如果当前有其他按键被按下，先释放它
        if self.key_pressed and self.current_key != key:
            self.release_key()
        
        # 更新当前按键
        self.current_key = key
        
        # 启动按键线程
        if self.key_thread is not None and self.key_thread.is_alive():
            # 停止当前线程
            self.stop_flag.set()
            self.key_thread.join(timeout=0.5)
            self.stop_flag.clear()
        
        # 创建新的按键线程
        self.key_thread = threading.Thread(
            target=self._key_press_worker,
            args=(key,),
            daemon=True
        )
        self.key_thread.start()
        
        logging.debug(f"开始长按按键: {key}")
    
    def release_key(self):
        """
        释放当前按下的按键
        """
        if not self.key_pressed:
            return
        
        # 停止按键线程
        if self.key_thread is not None and self.key_thread.is_alive():
            self.stop_flag.set()
            self.key_thread.join(timeout=0.5)
            self.stop_flag.clear()
        
        # 确保按键释放
        if self.current_key:
            try:
                pyautogui.keyUp(self.current_key)
                logging.debug(f"释放按键: {self.current_key}")
            except Exception as e:
                logging.error(f"释放按键失败: {str(e)}")
        
        # 重置状态
        self.key_pressed = False
        self.current_key = None
    
    def _key_press_worker(self, key: str):
        """
        按键长按工作线程
        
        Args:
            key: 要长按的按键
        """
        try:
            # 标记按键已按下
            self.key_pressed = True
            
            # 按下按键
            pyautogui.keyDown(key)
            logging.debug(f"按下按键: {key}")
            
            # 等待指定时间
            start_time = time.time()
            while time.time() - start_time < self.key_duration:
                # 检查是否收到停止信号
                if self.stop_flag.is_set():
                    break
                time.sleep(0.01)
            
            # 释放按键
            pyautogui.keyUp(key)
            logging.debug(f"释放按键: {key} (持续时间: {time.time() - start_time:.2f}秒)")
            
            # 标记按键已释放
            self.key_pressed = False
            
        except Exception as e:
            logging.error(f"按键操作失败: {str(e)}")
            # 确保按键释放
            try:
                pyautogui.keyUp(key)
            except:
                pass
            self.key_pressed = False
    
    def set_key_duration(self, duration: float):
        """
        设置按键持续时间
        
        Args:
            duration: 按键持续时间（秒）
        """
        self.key_duration = duration
        logging.info(f"按键持续时间已设置为: {duration}秒")
    
    def stop(self):
        """
        停止所有按键操作
        """
        self.release_key()
        logging.info("按键控制器已停止")


# 单例模式
_instance = None

def get_instance():
    """
    获取按键控制器单例
    
    Returns:
        KeyController实例
    """
    global _instance
    if _instance is None:
        _instance = KeyController()
    return _instance 