#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AutoFish热键管理模块

实现全局热键监听和处理功能。
"""

import logging
import threading
from typing import Optional, Callable
import keyboard

from modules.auto_fisher.config import get_config


class HotkeyManager:
    """热键管理器"""
    
    def __init__(self):
        """初始化热键管理器"""
        self.config = get_config()
        self.is_listening = False
        self.listener_thread: Optional[threading.Thread] = None
        
        # 回调函数
        self.start_callback: Optional[Callable] = None
        self.stop_callback: Optional[Callable] = None
        self.pause_callback: Optional[Callable] = None
        
        # 注册的热键
        self.registered_hotkeys = []
        
        logging.info("热键管理器初始化完成")
    
    def set_callbacks(self, start_callback: Callable = None, 
                     stop_callback: Callable = None, 
                     pause_callback: Callable = None):
        """
        设置回调函数
        
        Args:
            start_callback: 开始钓鱼回调
            stop_callback: 停止钓鱼回调
            pause_callback: 暂停钓鱼回调
        """
        self.start_callback = start_callback
        self.stop_callback = stop_callback
        self.pause_callback = pause_callback
    
    def start_listening(self):
        """开始热键监听"""
        if self.is_listening:
            logging.warning("热键监听已在运行")
            return
        
        try:
            # 获取热键配置
            hotkeys = self.config.get_hotkeys()
            
            # 注册热键
            self._register_hotkey(hotkeys.get('start', 'F1'), self._on_start_key)
            self._register_hotkey(hotkeys.get('stop', 'F2'), self._on_stop_key)
            self._register_hotkey(hotkeys.get('pause', 'F3'), self._on_pause_key)
            
            # 额外的紧急停止热键
            self._register_hotkey('ctrl+alt+q', self._on_emergency_stop)
            self._register_hotkey('esc', self._on_emergency_stop)
            
            self.is_listening = True
            logging.info("热键监听已启动")
            logging.info(f"开始钓鱼: {hotkeys.get('start', 'F1')}")
            logging.info(f"停止钓鱼: {hotkeys.get('stop', 'F2')}")
            logging.info(f"暂停钓鱼: {hotkeys.get('pause', 'F3')}")
            logging.info("紧急停止: Ctrl+Alt+Q 或 ESC")
            logging.info("紧急停止: 鼠标移动到屏幕左上角(0,0)")
            
        except Exception as e:
            logging.error(f"启动热键监听失败: {e}")
            self.is_listening = False
    
    def stop_listening(self):
        """停止热键监听"""
        if not self.is_listening:
            return
        
        try:
            # 移除所有注册的热键
            for hotkey in self.registered_hotkeys:
                keyboard.remove_hotkey(hotkey)
            
            self.registered_hotkeys.clear()
            self.is_listening = False
            logging.info("热键监听已停止")
            
        except Exception as e:
            logging.error(f"停止热键监听失败: {e}")
    
    def _register_hotkey(self, key: str, callback: Callable):
        """
        注册热键
        
        Args:
            key: 热键组合
            callback: 回调函数
        """
        try:
            hotkey_id = keyboard.add_hotkey(key, callback)
            self.registered_hotkeys.append(hotkey_id)
            logging.debug(f"注册热键成功: {key}")
        except Exception as e:
            logging.error(f"注册热键失败 {key}: {e}")
    
    def _on_start_key(self):
        """开始钓鱼热键处理"""
        logging.info("检测到开始钓鱼热键")
        if self.start_callback:
            try:
                self.start_callback()
            except Exception as e:
                logging.error(f"开始钓鱼回调执行失败: {e}")
    
    def _on_stop_key(self):
        """停止钓鱼热键处理"""
        logging.info("检测到停止钓鱼热键")
        if self.stop_callback:
            try:
                self.stop_callback()
            except Exception as e:
                logging.error(f"停止钓鱼回调执行失败: {e}")
    
    def _on_pause_key(self):
        """暂停钓鱼热键处理"""
        logging.info("检测到暂停钓鱼热键")
        if self.pause_callback:
            try:
                self.pause_callback()
            except Exception as e:
                logging.error(f"暂停钓鱼回调执行失败: {e}")
    
    def _on_emergency_stop(self):
        """紧急停止处理"""
        logging.warning("检测到紧急停止热键")
        if self.stop_callback:
            try:
                self.stop_callback()
                logging.info("紧急停止执行完成")
            except Exception as e:
                logging.error(f"紧急停止执行失败: {e}")
    
    def reload_config(self):
        """重新加载配置"""
        if self.is_listening:
            self.stop_listening()
            self.start_listening()
    
    def cleanup(self):
        """清理资源"""
        self.stop_listening()


# 全局热键管理器实例
_hotkey_manager_instance: Optional[HotkeyManager] = None


def get_hotkey_manager() -> HotkeyManager:
    """获取热键管理器实例"""
    global _hotkey_manager_instance
    if _hotkey_manager_instance is None:
        _hotkey_manager_instance = HotkeyManager()
    return _hotkey_manager_instance 