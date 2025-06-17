#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
业务逻辑管理器模块

该模块负责协调钓鱼脚本的整体业务逻辑，连接UI和后端功能模块。
"""

import os
import time
import logging
import threading
import keyboard
from typing import Optional, Callable, Dict, Any

# 导入相关模块
from modules.auto_fisher.config_manager import get_instance as get_config_manager
from modules.auto_fisher.model_detector import get_instance as get_model_detector
from modules.auto_fisher.input_simulator import get_instance as get_input_simulator
from modules.auto_fisher.fishing_state_machine import get_instance as get_state_machine
from modules.auto_fisher.fishing_state_machine import FishingState
from modules.auto_fisher.status_display import get_instance as get_status_display
from modules.auto_fisher.ocr_processor import get_instance as get_ocr_processor
from modules.auto_fisher.key_controller import get_instance as get_key_controller


class BusinessLogic:
    """
    业务逻辑管理器类
    
    负责协调钓鱼脚本的整体业务逻辑，连接UI和后端功能模块。
    """
    
    def __init__(self):
        """
        初始化业务逻辑管理器
        """
        # 获取相关模块实例
        self.config_manager = get_config_manager()
        self.model_detector = get_model_detector()
        self.input_simulator = get_input_simulator()
        self.state_machine = get_state_machine()
        self.status_display = get_status_display()
        self.ocr_processor = get_ocr_processor()
        self.key_controller = get_key_controller()
        
        # 获取热键配置
        self.hotkeys = self.config_manager.get_hotkeys()
        
        # 热键监听线程
        self.hotkey_thread = None
        self.is_hotkey_running = False
        
        # 状态回调（用于UI更新）
        self.status_callback: Optional[Callable[[str], None]] = None
        
        # 连接状态机的状态变化回调
        self.state_machine.set_state_callback(self._state_changed)
        
        # 设置OCR识别区域（默认为屏幕中央区域）
        self._setup_ocr_region()
        
        # 设置按键控制器的按键持续时间
        self.key_controller.set_key_duration(1.0)  # 1秒
        
        logging.info("业务逻辑管理器初始化完成")
    
    def _setup_ocr_region(self):
        """
        设置OCR识别区域
        
        默认设置为屏幕中央区域，可以通过配置文件修改
        """
        try:
            # 获取屏幕尺寸
            import pyautogui
            screen_width, screen_height = pyautogui.size()
            
            # 默认识别区域为屏幕中央
            x = screen_width // 4
            y = screen_height // 3
            width = screen_width // 2
            height = screen_height // 3
            
            # 设置OCR识别区域
            self.ocr_processor.set_roi(x, y, width, height)
            
            logging.info(f"OCR识别区域已设置: x={x}, y={y}, width={width}, height={height}")
            
        except Exception as e:
            logging.error(f"设置OCR识别区域失败: {str(e)}")
    
    def set_status_callback(self, callback: Callable[[str], None]):
        """
        设置状态回调函数，用于更新UI状态
        
        Args:
            callback: 状态回调函数
        """
        self.status_callback = callback
    
    def start_fishing(self):
        """
        开始钓鱼
        """
        if self.state_machine.is_running:
            logging.warning("钓鱼状态机已经在运行中")
            return
        
        try:
            # 启动状态显示
            self.status_display.start()
            
            # 启动状态机
            self.state_machine.start()
            
            # 更新状态
            self._update_status("钓鱼已启动，等待进入钓鱼状态...")
            
            logging.info("成功启动钓鱼")
            
        except Exception as e:
            logging.error(f"启动钓鱼失败: {str(e)}")
            self._update_status(f"启动钓鱼失败: {str(e)}")
    
    def stop_fishing(self):
        """
        停止钓鱼
        """
        if not self.state_machine.is_running:
            logging.warning("钓鱼状态机未在运行中")
            return
        
        try:
            # 停止状态机
            self.state_machine.stop()
            
            # 停止状态显示
            self.status_display.stop()
            
            # 确保OCR处理器停止
            self.ocr_processor.stop()
            
            # 确保释放所有按键
            self.key_controller.stop()
            
            # 更新状态
            self._update_status("钓鱼已停止")
            
            logging.info("成功停止钓鱼")
            
        except Exception as e:
            logging.error(f"停止钓鱼失败: {str(e)}")
            self._update_status(f"停止钓鱼失败: {str(e)}")
    
    def toggle_fishing(self):
        """
        切换钓鱼状态（开始/停止）
        """
        if self.state_machine.is_running:
            self.stop_fishing()
        else:
            self.start_fishing()
    
    def pause_fishing(self):
        """
        暂停钓鱼
        """
        if not self.state_machine.is_running or self.state_machine.is_paused:
            return
        
        try:
            # 暂停状态机
            self.state_machine.pause()
            
            # 更新状态
            self._update_status("钓鱼已暂停")
            
            logging.info("成功暂停钓鱼")
            
        except Exception as e:
            logging.error(f"暂停钓鱼失败: {str(e)}")
            self._update_status(f"暂停钓鱼失败: {str(e)}")
    
    def resume_fishing(self):
        """
        恢复钓鱼
        """
        if not self.state_machine.is_running or not self.state_machine.is_paused:
            return
        
        try:
            # 恢复状态机
            self.state_machine.resume()
            
            # 更新状态
            self._update_status("钓鱼已恢复")
            
            logging.info("成功恢复钓鱼")
            
        except Exception as e:
            logging.error(f"恢复钓鱼失败: {str(e)}")
            self._update_status(f"恢复钓鱼失败: {str(e)}")
    
    def toggle_pause(self):
        """
        切换暂停状态（暂停/恢复）
        """
        if not self.state_machine.is_running:
            return
        
        if self.state_machine.is_paused:
            self.resume_fishing()
        else:
            self.pause_fishing()
    
    def start_hotkey_listener(self):
        """
        启动热键监听
        """
        if self.is_hotkey_running:
            return
        
        self.is_hotkey_running = True
        
        # 注册热键
        self._register_hotkeys()
        
        # 启动热键监听线程
        self.hotkey_thread = threading.Thread(target=self._hotkey_listener, daemon=True)
        self.hotkey_thread.start()
        
        logging.info("热键监听已启动")
    
    def stop_hotkey_listener(self):
        """
        停止热键监听
        """
        if not self.is_hotkey_running:
            return
        
        self.is_hotkey_running = False
        
        # 注销所有热键
        keyboard.unhook_all()
        
        logging.info("热键监听已停止")
    
    def _register_hotkeys(self):
        """
        注册热键
        """
        try:
            # 注销现有热键
            keyboard.unhook_all()
            
            # 注册开始/停止热键
            keyboard.add_hotkey(self.hotkeys['start'], self.toggle_fishing)
            logging.info(f"已注册开始/停止热键: {self.hotkeys['start']}")
            
            # 注册紧急停止热键
            keyboard.add_hotkey(self.hotkeys['stop'], self.stop_fishing)
            logging.info(f"已注册紧急停止热键: {self.hotkeys['stop']}")
            
        except Exception as e:
            logging.error(f"注册热键失败: {str(e)}")
            self._update_status(f"注册热键失败: {str(e)}")
    
    def _hotkey_listener(self):
        """
        热键监听线程
        """
        try:
            # 一直运行直到标志位被设置为False
            while self.is_hotkey_running:
                time.sleep(0.1)
                
        except Exception as e:
            logging.error(f"热键监听线程出错: {str(e)}")
        
        logging.info("热键监听线程已退出")
    
    def update_hotkey(self, key: str, value: str):
        """
        更新热键设置
        
        Args:
            key: 热键名称
            value: 热键值
        """
        try:
            # 更新配置
            self.config_manager.update_config('hotkeys', key, value)
            self.config_manager.save_config()
            
            # 更新本地缓存
            self.hotkeys = self.config_manager.get_hotkeys()
            
            # 重新注册热键
            self._register_hotkeys()
            
            logging.info(f"已更新热键设置: {key} = {value}")
            
        except Exception as e:
            logging.error(f"更新热键设置失败: {str(e)}")
    
    def _state_changed(self, state: FishingState):
        """
        状态变更回调函数
        
        Args:
            state: 新状态
        """
        # 获取状态显示名称
        state_name = self._get_state_display_name(state)
        
        # 更新状态
        self._update_status(f"当前状态: {state_name}")
        
        # 更新状态显示
        try:
            logging.info(f"业务逻辑调用状态显示器更新状态: {state.name} -> {state_name}")
            self.status_display.update_state(state_name)
        except Exception as e:
            logging.error(f"更新状态显示时出错: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
    
    def _get_state_display_name(self, state: FishingState) -> str:
        """
        获取状态的显示名称
        
        Args:
            state: 状态枚举
        
        Returns:
            状态的显示名称
        """
        state_names = {
            FishingState.INITIALIZING: "初始化中",
            FishingState.IDLE: "空闲",
            FishingState.WAITING_FOR_FISH: "等待上钩",
            FishingState.FISH_DETECTED: "鱼上钩",
            FishingState.PULLING_NORMAL: "提线中",
            FishingState.PULLING_HALFWAY: "提线过半",
            FishingState.PULL_RIGHT: "向右拉",
            FishingState.PULL_LEFT: "向左拉",
            FishingState.SUCCESS: "钓鱼成功"
        }
        
        return state_names.get(state, "未知状态")
    
    def _update_status(self, status: str):
        """
        更新状态
        
        Args:
            status: 状态信息
        """
        if self.status_callback:
            try:
                self.status_callback(status)
            except Exception as e:
                logging.error(f"执行状态回调函数时出错: {str(e)}")
    
    def is_fishing_active(self) -> bool:
        """
        检查钓鱼是否处于活动状态
        
        Returns:
            是否活动
        """
        return self.state_machine.is_active()
    
    def get_current_state(self) -> FishingState:
        """
        获取当前状态
        
        Returns:
            当前状态
        """
        return self.state_machine.current_state
    
    def set_ocr_region(self, x: int, y: int, width: int, height: int):
        """
        设置OCR识别区域
        
        Args:
            x: 左上角x坐标
            y: 左上角y坐标
            width: 宽度
            height: 高度
        """
        self.ocr_processor.set_roi(x, y, width, height)
        logging.info(f"已手动设置OCR识别区域: x={x}, y={y}, width={width}, height={height}")


# 单例模式
_instance = None

def get_instance():
    """
    获取业务逻辑管理器单例
    
    Returns:
        BusinessLogic实例
    """
    global _instance
    if _instance is None:
        _instance = BusinessLogic()
    return _instance 