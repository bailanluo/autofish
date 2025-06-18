"""
Fisher钓鱼模块热键管理器
负责全局热键监听和处理

作者: AutoFish Team
版本: v1.0
创建时间: 2024-12-28
"""

import keyboard
import threading
from typing import Optional, Callable

from .config import fisher_config


class HotkeyManager:
    """热键管理器"""
    
    def __init__(self):
        """
        初始化热键管理器
        """
        self.is_active = False  # 热键是否激活
        self.hotkey_thread: Optional[threading.Thread] = None  # 热键线程
        self.fishing_active = False  # 钓鱼是否激活状态
        
        # 回调函数
        self.start_callback: Optional[Callable] = None
        self.stop_callback: Optional[Callable] = None
        self.emergency_callback: Optional[Callable] = None
        
        print("热键管理器初始化完成")
    
    def set_callbacks(self, start_callback: Optional[Callable] = None,
                     stop_callback: Optional[Callable] = None,
                     emergency_callback: Optional[Callable] = None) -> None:
        """
        设置热键回调函数
        
        Args:
            start_callback: 开始钓鱼回调
            stop_callback: 停止钓鱼回调
            emergency_callback: 紧急停止回调
        """
        self.start_callback = start_callback
        self.stop_callback = stop_callback
        self.emergency_callback = emergency_callback
    
    def set_fishing_active(self, active: bool) -> None:
        """
        设置钓鱼激活状态
        
        Args:
            active: 是否激活
        """
        self.fishing_active = active
    
    def start_listening(self) -> bool:
        """
        开始热键监听
        
        Returns:
            bool: 是否成功启动
        """
        if self.is_active:
            return True
        
        try:
            # 检查开始和停止热键是否相同
            if fisher_config.hotkey.start_fishing == fisher_config.hotkey.stop_fishing:
                # 相同热键，注册为切换功能
                keyboard.add_hotkey(fisher_config.hotkey.start_fishing, self._on_toggle_fishing)
                print(f"热键监听已启动:")
                print(f"  切换钓鱼: {fisher_config.hotkey.start_fishing} (开始/停止)")
            else:
                # 不同热键，分别注册
                keyboard.add_hotkey(fisher_config.hotkey.start_fishing, self._on_start_fishing)
                keyboard.add_hotkey(fisher_config.hotkey.stop_fishing, self._on_stop_fishing)
                print(f"热键监听已启动:")
                print(f"  开始钓鱼: {fisher_config.hotkey.start_fishing}")
                print(f"  停止钓鱼: {fisher_config.hotkey.stop_fishing}")
            
            # 注册紧急停止热键
            keyboard.add_hotkey(fisher_config.hotkey.emergency_stop, self._on_emergency_stop)
            print(f"  紧急停止: {fisher_config.hotkey.emergency_stop}")
            
            self.is_active = True
            return True
            
        except Exception as e:
            print(f"热键监听启动失败: {e}")
            return False
    
    def stop_listening(self) -> None:
        """停止热键监听"""
        if not self.is_active:
            return
        
        try:
            # 取消热键注册
            if fisher_config.hotkey.start_fishing == fisher_config.hotkey.stop_fishing:
                # 相同热键，只需取消一次
                keyboard.remove_hotkey(fisher_config.hotkey.start_fishing)
            else:
                # 不同热键，分别取消
                keyboard.remove_hotkey(fisher_config.hotkey.start_fishing)
                keyboard.remove_hotkey(fisher_config.hotkey.stop_fishing)
            
            keyboard.remove_hotkey(fisher_config.hotkey.emergency_stop)
            
            self.is_active = False
            print("热键监听已停止")
            
        except Exception as e:
            print(f"停止热键监听失败: {e}")
    
    def _on_toggle_fishing(self) -> None:
        """切换钓鱼状态热键处理"""
        print(f"热键触发: 切换钓鱼状态 ({fisher_config.hotkey.start_fishing})")
        
        if self.fishing_active:
            # 当前是激活状态，执行停止
            print("当前钓鱼激活，执行停止操作")
            if self.stop_callback:
                try:
                    self.stop_callback()
                except Exception as e:
                    print(f"停止钓鱼失败: {e}")
        else:
            # 当前是停止状态，执行开始
            print("当前钓鱼停止，执行开始操作")
            if self.start_callback:
                try:
                    self.start_callback()
                except Exception as e:
                    print(f"开始钓鱼失败: {e}")
    
    def _on_start_fishing(self) -> None:
        """开始钓鱼热键处理"""
        print(f"热键触发: 开始钓鱼 ({fisher_config.hotkey.start_fishing})")
        if self.start_callback:
            try:
                self.start_callback()
            except Exception as e:
                print(f"开始钓鱼回调失败: {e}")
    
    def _on_stop_fishing(self) -> None:
        """停止钓鱼热键处理"""
        print(f"热键触发: 停止钓鱼 ({fisher_config.hotkey.stop_fishing})")
        if self.stop_callback:
            try:
                self.stop_callback()
            except Exception as e:
                print(f"停止钓鱼回调失败: {e}")
    
    def _on_emergency_stop(self) -> None:
        """紧急停止热键处理"""
        print(f"热键触发: 紧急停止 ({fisher_config.hotkey.emergency_stop})")
        if self.emergency_callback:
            try:
                self.emergency_callback()
            except Exception as e:
                print(f"紧急停止回调失败: {e}")
    
    def update_hotkeys(self) -> bool:
        """
        更新热键配置
        
        Returns:
            bool: 是否更新成功
        """
        if self.is_active:
            # 重新启动热键监听
            self.stop_listening()
            return self.start_listening()
        return True
    
    def cleanup(self) -> None:
        """清理资源"""
        print("清理热键管理器资源")
        self.stop_listening()

# 全局热键管理器实例
hotkey_manager = HotkeyManager() 