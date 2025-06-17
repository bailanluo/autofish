"""
Fisher钓鱼模块输入控制器
负责鼠标点击和键盘按键操作，支持多线程安全操作

作者: AutoFish Team
版本: v1.0
创建时间: 2024-12-28
"""

import time
import random
import threading
from typing import Optional
import pyautogui
import keyboard

from .config import fisher_config


class InputController:
    """输入控制器"""
    
    def __init__(self):
        """
        初始化输入控制器
        """
        # 鼠标点击线程相关
        self.click_thread: Optional[threading.Thread] = None  # 点击线程
        self.click_event = threading.Event()  # 点击控制事件
        self.click_running = threading.Event()  # 点击运行状态
        self.stop_clicking_event = threading.Event()  # 停止点击事件
        
        # 键盘按键线程相关
        self.key_thread: Optional[threading.Thread] = None  # 按键线程
        self.key_queue = []  # 按键队列
        self.key_lock = threading.Lock()  # 按键锁
        
        # 配置pyautogui
        pyautogui.FAILSAFE = True  # 启用失效保护
        pyautogui.PAUSE = 0.01  # 设置操作间隔
        
        print("输入控制器初始化完成")
    
    def _click_worker(self) -> None:
        """
        鼠标点击工作线程
        持续执行鼠标点击，直到收到停止信号
        """
        print("鼠标点击线程启动")
        
        while not self.stop_clicking_event.is_set():
            # 等待点击信号
            if self.click_event.wait(timeout=0.1):
                # 执行点击
                try:
                    # 生成随机点击间隔
                    delay = random.uniform(
                        fisher_config.timing.click_delay_min,
                        fisher_config.timing.click_delay_max
                    )
                    
                    # 鼠标左键按下
                    pyautogui.mouseDown(button='left')
                    time.sleep(delay)
                    
                    # 鼠标左键弹起
                    pyautogui.mouseUp(button='left')
                    time.sleep(delay)
                    
                except Exception as e:
                    print(f"鼠标点击失败: {e}")
                    break
            
            # 检查是否暂停点击
            if not self.click_running.is_set():
                self.click_event.clear()
        
        print("鼠标点击线程结束")
    
    def start_clicking(self) -> bool:
        """
        开始快速点击
        
        Returns:
            bool: 是否成功启动
        """
        try:
            if self.click_thread and self.click_thread.is_alive():
                print("点击线程已在运行")
                return True
            
            # 重置停止信号
            self.stop_clicking_event.clear()
            
            # 创建并启动点击线程
            self.click_thread = threading.Thread(target=self._click_worker, daemon=True)
            self.click_thread.start()
            
            # 启动点击
            self.click_running.set()
            self.click_event.set()
            
            print("快速点击已启动")
            return True
            
        except Exception as e:
            print(f"启动点击失败: {e}")
            return False
    
    def pause_clicking(self) -> None:
        """暂停点击"""
        self.click_running.clear()
        self.click_event.clear()
        print("鼠标点击已暂停")
    
    def resume_clicking(self) -> None:
        """恢复点击"""
        if self.click_thread and self.click_thread.is_alive():
            self.click_running.set()
            self.click_event.set()
            print("鼠标点击已恢复")
        else:
            print("点击线程未运行，尝试重新启动")
            self.start_clicking()
    
    def stop_clicking(self) -> None:
        """停止点击"""
        try:
            # 设置停止信号
            self.stop_clicking_event.set()
            self.click_event.clear()
            self.click_running.clear()
            
            # 等待线程结束
            if self.click_thread and self.click_thread.is_alive():
                self.click_thread.join(timeout=2.0)
            
            print("快速点击已停止")
            
        except Exception as e:
            print(f"停止点击失败: {e}")
    
    def is_clicking(self) -> bool:
        """
        检查是否正在点击
        
        Returns:
            bool: 是否正在点击
        """
        return (self.click_thread and 
                self.click_thread.is_alive() and 
                self.click_running.is_set())
    
    def press_key(self, key: str, duration: Optional[float] = None) -> bool:
        """
        按下指定按键
        
        Args:
            key: 按键名称 ('a', 'd', 'f' 等)
            duration: 按键持续时间，None表示使用配置的默认时间
            
        Returns:
            bool: 是否成功按键
        """
        try:
            if duration is None:
                duration = fisher_config.timing.key_press_time
            
            # 按下按键
            keyboard.press(key)
            time.sleep(duration)
            keyboard.release(key)
            
            print(f"按键 '{key}' 持续 {duration:.2f}秒")
            return True
            
        except Exception as e:
            print(f"按键 '{key}' 失败: {e}")
            return False
    
    def press_key_threaded(self, key: str, duration: Optional[float] = None) -> bool:
        """
        在单独线程中按下指定按键
        
        Args:
            key: 按键名称
            duration: 按键持续时间
            
        Returns:
            bool: 是否成功启动按键线程
        """
        try:
            def key_worker():
                self.press_key(key, duration)
            
            key_thread = threading.Thread(target=key_worker, daemon=True)
            key_thread.start()
            
            return True
            
        except Exception as e:
            print(f"启动按键线程失败: {e}")
            return False
    
    def left_click(self, x: Optional[int] = None, y: Optional[int] = None) -> bool:
        """
        单次鼠标左键点击
        
        Args:
            x: 点击x坐标，None表示当前位置
            y: 点击y坐标，None表示当前位置
            
        Returns:
            bool: 是否成功点击
        """
        try:
            if x is not None and y is not None:
                pyautogui.click(x, y, button='left')
            else:
                pyautogui.click(button='left')
            
            print(f"鼠标左键点击 ({x}, {y})")
            return True
            
        except Exception as e:
            print(f"鼠标点击失败: {e}")
            return False
    
    def left_click_hold(self, duration: Optional[float] = None) -> bool:
        """
        鼠标左键长按
        
        Args:
            duration: 长按持续时间，None表示使用配置的抛竿时间
            
        Returns:
            bool: 是否成功长按
        """
        try:
            if duration is None:
                duration = fisher_config.timing.cast_hold_time
            
            # 按下鼠标左键
            pyautogui.mouseDown(button='left')
            time.sleep(duration)
            pyautogui.mouseUp(button='left')
            
            print(f"鼠标左键长按 {duration:.2f}秒")
            return True
            
        except Exception as e:
            print(f"鼠标长按失败: {e}")
            return False
    
    def handle_direction_key(self, direction_state: int) -> bool:
        """
        根据方向状态按下对应按键
        
        Args:
            direction_state: 方向状态 (4: 向右拉, 5: 向左拉)
            
        Returns:
            bool: 是否成功按键
        """
        if direction_state == 4:  # 向右拉
            return self.press_key('d')
        elif direction_state == 5:  # 向左拉
            return self.press_key('a')
        else:
            print(f"未知的方向状态: {direction_state}")
            return False
    
    def handle_success_key(self) -> bool:
        """
        处理钓鱼成功状态的按键 (f键)
        
        Returns:
            bool: 是否成功按键
        """
        return self.press_key('f')
    
    def wait_and_handle_success(self, wait_time: Optional[float] = None) -> bool:
        """
        等待后处理钓鱼成功状态
        
        Args:
            wait_time: 等待时间，None表示使用配置的成功等待时间
            
        Returns:
            bool: 是否成功处理
        """
        try:
            if wait_time is None:
                wait_time = fisher_config.timing.success_wait_time
            
            # 等待指定时间
            time.sleep(wait_time)
            
            # 按下f键
            return self.handle_success_key()
            
        except Exception as e:
            print(f"处理成功状态失败: {e}")
            return False
    
    def cast_rod(self) -> bool:
        """
        抛竿操作（长按鼠标左键2秒）
        
        Returns:
            bool: 是否成功抛竿
        """
        print("执行抛竿操作")
        return self.left_click_hold()
    
    def get_input_status(self) -> dict:
        """
        获取输入控制器状态
        
        Returns:
            dict: 控制器状态信息
        """
        return {
            'clicking': self.is_clicking(),
            'click_thread_alive': self.click_thread.is_alive() if self.click_thread else False,
            'click_running': self.click_running.is_set(),
            'stop_signal': self.stop_clicking_event.is_set()
        }
    
    def emergency_stop(self) -> None:
        """紧急停止所有输入操作"""
        print("紧急停止所有输入操作")
        
        # 停止鼠标点击
        self.stop_clicking()
        
        # 释放所有按键
        try:
            keyboard.release('a')
            keyboard.release('d')
            keyboard.release('f')
        except:
            pass
        
        # 释放鼠标按键
        try:
            pyautogui.mouseUp(button='left')
        except:
            pass
    
    def cleanup(self) -> None:
        """清理资源"""
        print("清理输入控制器资源")
        self.emergency_stop()

# 全局输入控制器实例
input_controller = InputController() 