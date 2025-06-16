"""
热键监听模块
提供全局热键监听功能
"""

import os
import sys
import threading
from typing import Dict, Callable
import keyboard

# 添加主项目路径以使用logger
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from modules.logger import setup_logger


class HotkeyListener:
    """全局热键监听器"""
    
    def __init__(self, hotkey_config: Dict[str, str], callbacks: Dict[str, Callable]):
        """
        初始化热键监听器
        
        Args:
            hotkey_config: 热键配置字典 {'select_region': 'ctrl+alt+y', 'quick_capture': 'y'}
            callbacks: 回调函数字典 {'select_region': func1, 'quick_capture': func2}
        """
        self.hotkey_config = hotkey_config  # 热键配置
        self.callbacks = callbacks  # 回调函数
        self.logger = setup_logger('HotkeyListener')  # 日志记录器
        self.is_listening = False  # 监听状态
        self.is_paused = False  # 暂停状态
        self.listener_thread = None  # 监听线程
        self.capture_enabled = False  # 快速截图是否启用（只有设置好区域和类别后才启用）
        self.capture_paused = False  # 快速截图是否被暂停
        
    def start_listening(self):
        """启动热键监听"""
        if not self.is_listening:
            self.is_listening = True
            self.listener_thread = threading.Thread(target=self._listen_hotkeys, daemon=True)
            self.listener_thread.start()
            self.logger.info("热键监听已启动")
    
    def stop_listening(self):
        """停止热键监听"""
        if self.is_listening:
            self.is_listening = False
            if self.listener_thread:
                self.listener_thread.join(timeout=1)
            self.logger.info("热键监听已停止")
    
    def pause_listening(self):
        """暂停热键监听（临时停用，不关闭线程）"""
        if self.is_listening and not self.is_paused:
            self.is_paused = True
            keyboard.unhook_all()  # 取消所有热键注册
            self.logger.info("热键监听已暂停")
    
    def resume_listening(self):
        """恢复热键监听"""
        if self.is_listening and self.is_paused:
            self.is_paused = False
            # 重新注册热键
            for hotkey_name, callback_name in [
                ('select_region', 'select_region'),
                ('quick_capture', 'quick_capture'),
                ('pause_capture', 'pause_capture')
            ]:
                if hotkey_name in self.hotkey_config:
                    hotkey = self.hotkey_config[hotkey_name]
                    
                    # 为快速截图使用安全回调，其他使用原始回调
                    if callback_name == 'quick_capture':
                        callback = self._safe_quick_capture
                    elif callback_name in self.callbacks:
                        callback = self.callbacks[callback_name]
                    else:
                        continue
                    
                    keyboard.add_hotkey(hotkey, callback)
            self.logger.info("热键监听已恢复")
    
    def enable_capture(self):
        """启用快速截图热键（设置好区域和类别后调用）"""
        self.capture_enabled = True
        self.logger.info("快速截图热键已启用")
    
    def disable_capture(self):
        """禁用快速截图热键"""
        self.capture_enabled = False
        self.logger.info("快速截图热键已禁用")
    
    def pause_capture(self):
        """暂停快速截图（简单开关）"""
        self.capture_paused = True
        self.logger.info("快速截图已暂停")
    
    def resume_capture(self):
        """恢复快速截图（简单开关）"""
        self.capture_paused = False
        self.logger.info("快速截图已恢复")
    
    def _safe_quick_capture(self):
        """安全的快速截图回调（检查是否启用和暂停）"""
        if not self.capture_enabled:
            self.logger.warning("快速截图热键被触发但未启用，需要先设置截图区域和类别")
            return
        
        if self.capture_paused:
            self.logger.info("快速截图已暂停")
            return
        
        # 调用原始的快速截图回调
        if 'quick_capture' in self.callbacks:
            self.callbacks['quick_capture']()
    
    def _listen_hotkeys(self):
        """热键监听主循环"""
        try:
            # 注册热键
            for hotkey_name, callback_name in [
                ('select_region', 'select_region'),
                ('quick_capture', 'quick_capture'),
                ('pause_capture', 'pause_capture')
            ]:
                if hotkey_name in self.hotkey_config:
                    hotkey = self.hotkey_config[hotkey_name]
                    
                    # 为快速截图使用安全回调，其他使用原始回调
                    if callback_name == 'quick_capture':
                        callback = self._safe_quick_capture
                    elif callback_name in self.callbacks:
                        callback = self.callbacks[callback_name]
                    else:
                        continue
                    
                    keyboard.add_hotkey(hotkey, callback)
                    self.logger.info(f"注册热键: {hotkey} -> {callback_name}")
            
            # 监听循环
            while self.is_listening:
                keyboard.wait()  # 等待热键事件
                if not self.is_listening:
                    break
            
        except Exception as e:
            self.logger.error(f"热键监听异常: {e}")
        finally:
            # 清理热键注册
            keyboard.unhook_all()
            self.logger.info("热键监听已清理")
    
    def update_hotkeys(self, new_hotkey_config: Dict[str, str]):
        """
        更新热键配置
        
        Args:
            new_hotkey_config: 新的热键配置
        """
        # 先停止监听
        was_listening = self.is_listening
        if was_listening:
            self.stop_listening()
        
        # 更新配置
        self.hotkey_config.update(new_hotkey_config)
        self.logger.info(f"热键配置已更新: {new_hotkey_config}")
        
        # 重新启动监听
        if was_listening:
            self.start_listening()
    
    def is_valid_hotkey(self, hotkey_str: str) -> bool:
        """
        验证热键字符串是否有效
        
        Args:
            hotkey_str: 热键字符串，如 'ctrl+alt+y'
            
        Returns:
            是否有效
        """
        try:
            # 尝试解析热键
            keyboard.parse_hotkey(hotkey_str)
            return True
        except Exception:
            return False
    
    def get_hotkey_display_name(self, hotkey_str: str) -> str:
        """
        获取热键的显示名称
        
        Args:
            hotkey_str: 热键字符串
            
        Returns:
            格式化的显示名称
        """
        try:
            # 将热键字符串格式化为更友好的显示格式
            parts = hotkey_str.lower().split('+')
            display_parts = []
            
            for part in parts:
                if part == 'ctrl':
                    display_parts.append('Ctrl')
                elif part == 'alt':
                    display_parts.append('Alt')
                elif part == 'shift':
                    display_parts.append('Shift')
                elif part == 'cmd':
                    display_parts.append('Cmd')
                elif part == 'space':
                    display_parts.append('Space')
                elif part == 'enter':
                    display_parts.append('Enter')
                elif part == 'tab':
                    display_parts.append('Tab')
                elif part == 'esc':
                    display_parts.append('Esc')
                elif part.startswith('f') and part[1:].isdigit():
                    display_parts.append(part.upper())
                else:
                    display_parts.append(part.upper())
            
            return '+'.join(display_parts)
        except Exception:
            return hotkey_str.upper()
    
    def get_current_hotkeys(self) -> Dict[str, str]:
        """获取当前热键配置"""
        return self.hotkey_config.copy()
    
    def validate_hotkey_combination(self, hotkey_str: str) -> tuple[bool, str]:
        """
        验证热键组合并返回错误信息
        
        Args:
            hotkey_str: 热键字符串
            
        Returns:
            (是否有效, 错误信息)
        """
        if not hotkey_str or not hotkey_str.strip():
            return False, "热键不能为空"
        
        try:
            # 尝试解析热键
            parsed = keyboard.parse_hotkey(hotkey_str)
            
            # 检查是否包含有效的键
            if not parsed:
                return False, "无效的热键格式"
            
            # 检查是否只包含修饰键
            has_main_key = False
            for key_combination in parsed:
                for key in key_combination:
                    if key not in ['ctrl', 'alt', 'shift', 'cmd', 'win']:
                        has_main_key = True
                        break
                if has_main_key:
                    break
            
            if not has_main_key:
                return False, "热键必须包含至少一个非修饰键"
            
            return True, ""
            
        except Exception as e:
            return False, f"热键格式错误: {str(e)}" 