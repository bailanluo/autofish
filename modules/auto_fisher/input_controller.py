#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AutoFish输入控制器模块

负责鼠标和键盘的模拟操作。
"""

import time
import random
import logging
import threading
import pyautogui
from typing import Optional

from modules.auto_fisher.config import get_config


class InputController:
    """输入控制器类"""
    
    def __init__(self):
        """初始化输入控制器"""
        self.config = get_config()
        
        # 设置pyautogui参数
        pyautogui.FAILSAFE = True   # 启用fail-safe机制，鼠标移动到左上角(0,0)可紧急停止程序
        pyautogui.PAUSE = 0.01
        
        # 点击相关
        self.clicking_thread: Optional[threading.Thread] = None
        self.clicking_active = False
        self.click_lock = threading.Lock()
        
        # 按键相关
        self.current_key_pressed = None
        self.key_lock = threading.Lock()
        
        logging.info("输入控制器初始化完成")
    
    def start_rapid_clicking(self):
        """开始快速点击"""
        with self.click_lock:
            if self.clicking_active:
                return
            
            self.clicking_active = True
            self.clicking_thread = threading.Thread(target=self._rapid_click_worker, daemon=True)
            self.clicking_thread.start()
            logging.info("开始快速点击")
    
    def stop_rapid_clicking(self):
        """停止快速点击"""
        with self.click_lock:
            if not self.clicking_active:
                return
            
            self.clicking_active = False
            if self.clicking_thread and self.clicking_thread.is_alive():
                self.clicking_thread.join(timeout=1.0)
            
            logging.info("停止快速点击")
    
    def _rapid_click_worker(self):
        """快速点击工作线程"""
        min_interval = self.config.get('fishing.click_interval_min', 0.054)
        max_interval = self.config.get('fishing.click_interval_max', 0.127)
        
        while self.clicking_active:
            try:
                # 随机点击间隔
                press_time = random.uniform(min_interval, max_interval)
                release_time = random.uniform(min_interval, max_interval)
                
                # 鼠标按下
                pyautogui.mouseDown()
                time.sleep(press_time)
                
                # 鼠标释放
                pyautogui.mouseUp()
                time.sleep(release_time)
                
            except Exception as e:
                logging.error(f"快速点击出错: {e}")
                break
    
    def press_key_temporarily(self, key: str, duration: float = 0.1):
        """
        临时按下按键
        
        Args:
            key: 按键名称
            duration: 按住时间
        """
        try:
            pyautogui.keyDown(key)
            time.sleep(duration)
            pyautogui.keyUp(key)
            logging.debug(f"临时按键: {key}, 持续时间: {duration}s")
        except Exception as e:
            logging.error(f"临时按键失败: {e}")
    
    def hold_key(self, key: str):
        """
        持续按住按键
        
        Args:
            key: 按键名称
        """
        with self.key_lock:
            try:
                # 先释放当前按键
                if self.current_key_pressed:
                    pyautogui.keyUp(self.current_key_pressed)
                
                # 按住新按键
                if key:
                    pyautogui.keyDown(key)
                    self.current_key_pressed = key
                    logging.debug(f"持续按住按键: {key}")
                else:
                    self.current_key_pressed = None
                    
            except Exception as e:
                logging.error(f"持续按键失败: {e}")
    
    def release_all_keys(self):
        """释放所有按键"""
        with self.key_lock:
            try:
                if self.current_key_pressed:
                    pyautogui.keyUp(self.current_key_pressed)
                    logging.debug(f"释放按键: {self.current_key_pressed}")
                    self.current_key_pressed = None
            except Exception as e:
                logging.error(f"释放按键失败: {e}")
    
    def single_click(self):
        """单次点击"""
        try:
            pyautogui.click()
            logging.debug("单次点击")
        except Exception as e:
            logging.error(f"单次点击失败: {e}")
    
    def hold_click(self, duration: float = 2.0):
        """
        长按点击
        
        Args:
            duration: 按住时间
        """
        try:
            pyautogui.mouseDown()
            time.sleep(duration)
            pyautogui.mouseUp()
            logging.debug(f"长按点击: {duration}s")
        except Exception as e:
            logging.error(f"长按点击失败: {e}")
    
    def handle_direction_key(self, direction: str):
        """
        处理方向按键
        
        Args:
            direction: 方向 ('left' 或 'right')
        """
        key_mapping = self.config.get('key_mapping', {})
        
        if direction == 'left':
            key = key_mapping.get('left_pull', 'a')
            self.hold_key(key)
        elif direction == 'right':
            key = key_mapping.get('right_pull', 'f')
            self.hold_key(key)
        else:
            # 释放所有按键
            self.release_all_keys()
    
    def confirm_action(self):
        """确认动作（钓鱼成功时使用）"""
        try:
            key_mapping = self.config.get('key_mapping', {})
            confirm_key = key_mapping.get('confirm', 'f')
            self.press_key_temporarily(confirm_key, 0.1)
            logging.debug(f"确认动作: {confirm_key}")
        except Exception as e:
            logging.error(f"确认动作失败: {e}")
    
    def cast_fishing_rod(self):
        """抛竿动作"""
        try:
            cast_duration = self.config.get('fishing.cast_hold_time', 2.0)
            key_mapping = self.config.get('key_mapping', {})
            cast_action = key_mapping.get('cast', 'left_mouse')
            
            if cast_action == 'left_mouse':
                self.hold_click(cast_duration)
            else:
                pyautogui.keyDown(cast_action)
                time.sleep(cast_duration)
                pyautogui.keyUp(cast_action)
            
            logging.info(f"抛竿动作: {cast_action}, 持续时间: {cast_duration}s")
        except Exception as e:
            logging.error(f"抛竿动作失败: {e}")
    
    def is_clicking(self) -> bool:
        """检查是否正在点击"""
        return self.clicking_active
    
    def cleanup(self):
        """清理资源"""
        self.stop_rapid_clicking()
        self.release_all_keys()
        logging.info("输入控制器资源清理完成")


# 全局输入控制器实例
_input_controller_instance: Optional[InputController] = None


def get_input_controller() -> InputController:
    """获取输入控制器实例"""
    global _input_controller_instance
    if _input_controller_instance is None:
        _input_controller_instance = InputController()
    return _input_controller_instance 