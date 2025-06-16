#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
输入模拟器模块

该模块负责模拟鼠标和键盘操作，包括点击、按键和组合键等。
"""

import time
import random
import logging
from typing import Tuple, Union, Optional
import pyautogui

# 导入配置管理器
from modules.auto_fisher.config_manager import get_instance as get_config_manager


class InputSimulator:
    """
    输入模拟器类
    
    负责模拟用户的鼠标和键盘输入操作。
    """

    def __init__(self):
        """
        初始化输入模拟器
        """
        # 获取配置管理器
        self.config_manager = get_config_manager()
        
        # 点击间隔范围
        self.click_interval_min, self.click_interval_max = self.config_manager.get_click_interval()
        
        # 按键操作时间
        self.key_durations = self.config_manager.get_key_press_duration()
        
        # 点击减速因子
        self.click_slowdown_factor = self.config_manager.get_click_slowdown_factor()
        
        # 安全模式设置
        self.safe_mode = True  # 安全模式下，会添加随机延迟
        
        # 设置pyautogui的安全设置
        pyautogui.PAUSE = 0.01  # 操作之间的最小间隔
        pyautogui.FAILSAFE = True  # 启用故障安全（将鼠标移到屏幕角落可中断操作）
        
        logging.info("输入模拟器初始化完成")

    def set_click_interval(self, min_interval: float, max_interval: float):
        """
        设置点击间隔范围
        
        Args:
            min_interval: 最小间隔时间（秒）
            max_interval: 最大间隔时间（秒）
        """
        self.click_interval_min = min_interval
        self.click_interval_max = max_interval
        logging.info(f"点击间隔已更新: {min_interval}-{max_interval}秒")

    def get_random_duration(self) -> float:
        """
        获取随机点击间隔时间
        
        Returns:
            随机生成的时间间隔（秒）
        """
        return random.uniform(self.click_interval_min, self.click_interval_max)

    def slow_click_interval(self, enable: bool = True):
        """
        减慢或恢复点击间隔（用于方向操作期间）
        
        Args:
            enable: 是否启用减速
        """
        if enable:
            self.click_interval_min *= self.click_slowdown_factor
            self.click_interval_max *= self.click_slowdown_factor
            logging.debug(f"点击间隔已减慢: {self.click_interval_min}-{self.click_interval_max}秒")
        else:
            self.click_interval_min /= self.click_slowdown_factor
            self.click_interval_max /= self.click_slowdown_factor
            logging.debug(f"点击间隔已恢复: {self.click_interval_min}-{self.click_interval_max}秒")

    def move_mouse(self, x: int, y: int, duration: float = 0.1):
        """
        移动鼠标到指定位置
        
        Args:
            x: 目标X坐标
            y: 目标Y坐标
            duration: 移动持续时间（秒）
        """
        try:
            pyautogui.moveTo(x, y, duration=duration)
            logging.debug(f"鼠标已移动到位置: ({x}, {y})")
        except Exception as e:
            logging.error(f"移动鼠标失败: {str(e)}")

    def click(self, button: str = 'left', delay: Optional[float] = None):
        """
        模拟鼠标点击
        
        Args:
            button: 鼠标按键 ('left', 'right', 'middle')
            delay: 点击延迟时间，如果为None则使用随机间隔
        """
        try:
            # 确定点击延迟
            click_delay = delay if delay is not None else self.get_random_duration()
            
            # 执行点击 - 使用按下和释放分开操作，减少延迟
            pyautogui.mouseDown(button=button)
            pyautogui.mouseUp(button=button)
            
            # 使用精确的时间延迟，但不阻塞主线程
            start_time = time.perf_counter()
            
            # 对于非常短的延迟，使用更精确的循环等待
            if click_delay < 0.01:
                while time.perf_counter() - start_time < click_delay:
                    pass  # 紧凑循环，最大化点击速率
            else:
                # 对于较长的延迟，使用sleep以减少CPU使用
                remaining = click_delay
                while remaining > 0:
                    # 使用短暂的睡眠，避免长时间阻塞
                    sleep_time = min(0.001, remaining)
                    time.sleep(sleep_time)
                    remaining = click_delay - (time.perf_counter() - start_time)
            
        except Exception as e:
            # 简化错误处理，不记录日志以提高性能
            pass

    def mouse_down(self, button: str = 'left'):
        """
        按下鼠标按键
        
        Args:
            button: 鼠标按键 ('left', 'right', 'middle')
        """
        try:
            pyautogui.mouseDown(button=button)
            logging.debug(f"按下鼠标{button}键")
        except Exception as e:
            logging.error(f"按下鼠标按键失败: {str(e)}")

    def mouse_up(self, button: str = 'left'):
        """
        释放鼠标按键
        
        Args:
            button: 鼠标按键 ('left', 'right', 'middle')
        """
        try:
            pyautogui.mouseUp(button=button)
            logging.debug(f"释放鼠标{button}键")
        except Exception as e:
            logging.error(f"释放鼠标按键失败: {str(e)}")

    def key_press(self, key: str, duration: Optional[float] = None):
        """
        模拟键盘按键按下并释放
        
        Args:
            key: 按键名称
            duration: 按键持续时间，如果为None则使用默认时间
        """
        try:
            # 确定按键持续时间
            press_duration = duration if duration is not None else self.key_durations['direction_key']
            
            # 按下按键
            pyautogui.keyDown(key)
            logging.debug(f"按下按键: {key}, 持续时间: {press_duration:.3f}秒")
            
            # 等待指定时间
            time.sleep(press_duration)
            
            # 释放按键
            pyautogui.keyUp(key)
            logging.debug(f"释放按键: {key}")
            
        except Exception as e:
            logging.error(f"键盘按键操作失败: {str(e)}")
            # 确保按键释放
            try:
                pyautogui.keyUp(key)
            except:
                pass

    def key_down(self, key: str):
        """
        按下键盘按键
        
        Args:
            key: 按键名称
        """
        try:
            pyautogui.keyDown(key)
            logging.debug(f"按下按键: {key}")
        except Exception as e:
            logging.error(f"按下按键失败: {str(e)}")

    def key_up(self, key: str):
        """
        释放键盘按键
        
        Args:
            key: 按键名称
        """
        try:
            pyautogui.keyUp(key)
            logging.debug(f"释放按键: {key}")
        except Exception as e:
            logging.error(f"释放按键失败: {str(e)}")

    def press_hotkey(self, *keys):
        """
        模拟组合键
        
        Args:
            *keys: 要按下的按键序列
        """
        try:
            pyautogui.hotkey(*keys)
            logging.debug(f"执行组合键: {'+'.join(keys)}")
        except Exception as e:
            logging.error(f"组合键操作失败: {str(e)}")
            # 确保所有按键释放
            for key in keys:
                try:
                    pyautogui.keyUp(key)
                except:
                    pass
    
    def mouse_long_press(self, button: str = 'left', duration: Optional[float] = None):
        """
        鼠标长按并释放
        
        Args:
            button: 鼠标按键 ('left', 'right', 'middle')
            duration: 长按持续时间，如果为None则使用默认时间
        """
        try:
            # 确定长按持续时间
            press_duration = duration if duration is not None else self.key_durations['mouse_long_press']
            
            # 按下鼠标
            pyautogui.mouseDown(button=button)
            logging.debug(f"鼠标{button}键长按, 持续时间: {press_duration:.3f}秒")
            
            # 等待指定时间
            time.sleep(press_duration)
            
            # 释放鼠标
            pyautogui.mouseUp(button=button)
            logging.debug(f"释放鼠标{button}键")
            
        except Exception as e:
            logging.error(f"鼠标长按操作失败: {str(e)}")
            # 确保鼠标释放
            try:
                pyautogui.mouseUp(button=button)
            except:
                pass

    def rapid_click(self, button: str = 'left', count: int = 1):
        """
        快速连续点击
        
        Args:
            button: 鼠标按键 ('left', 'right', 'middle')
            count: 点击次数
        """
        try:
            for _ in range(count):
                # 使用更高效的点击方法
                self.direct_click(button)
                
                # 生成随机点击间隔，但使用更短的间隔
                click_delay = random.uniform(
                    self.click_interval_min * 0.8,  # 减少20%的最小间隔
                    self.click_interval_max * 0.8   # 减少20%的最大间隔
                )
                
                # 使用高精度延迟
                start_time = time.perf_counter()
                while time.perf_counter() - start_time < click_delay:
                    pass  # 紧凑循环，最大化点击速率
                
        except Exception as e:
            # 简化错误处理，不记录日志以提高性能
            pass
    
    def direct_click(self, button: str = 'left'):
        """
        直接点击 - 使用最低级别的API进行点击，避免PyAutoGUI的额外开销
        
        Args:
            button: 鼠标按键 ('left', 'right', 'middle')
        """
        try:
            # 使用PyAutoGUI的底层API直接点击，避免额外检查
            pyautogui._mouseDown(button)
            pyautogui._mouseUp(button)
        except Exception:
            # 如果底层API失败，回退到标准方法
            try:
                pyautogui.click(button=button)
            except:
                pass
                
    def cycle_click(self, button: str = 'left'):
        """
        循环点击 - 按下一段时间后弹起，再弹起一段时间后按下
        
        按下持续0.054s-0.127s，弹起也持续0.054s-0.127s，形成一个完整的点击循环
        
        Args:
            button: 鼠标按键 ('left', 'right', 'middle')
        """
        try:
            # 按下鼠标
            pyautogui.mouseDown(button=button)
            
            # 等待随机时间后弹起
            down_time = random.uniform(self.click_interval_min, self.click_interval_max)
            time.sleep(down_time)
            
            # 弹起鼠标
            pyautogui.mouseUp(button=button)
            
            # 返回按下持续时间，供调用者决定下一次按下的时间
            return down_time
            
        except Exception as e:
            # 确保鼠标弹起
            try:
                pyautogui.mouseUp(button=button)
            except:
                pass
            return 0.1  # 出错时返回默认值


# 单例模式
_instance = None

def get_instance():
    """
    获取输入模拟器单例
    
    Returns:
        InputSimulator实例
    """
    global _instance
    if _instance is None:
        _instance = InputSimulator()
    return _instance 