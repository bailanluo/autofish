"""
Fisher钓鱼模块输入控制器
负责鼠标点击和键盘按键操作，支持多线程安全操作

作者: AutoFish Team
版本: v1.0.1
创建时间: 2024-12-28
更新时间: 2025-01-17
修复历史: v1.0.1 - 集成统一日志系统
"""

import time
import random
import threading
from typing import Optional
import pyautogui
import keyboard
import ctypes

# Windows API用于游戏兼容的鼠标移动

# 导入统一日志系统
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from logger import setup_logger

from .config import fisher_config

# 设置日志记录器
logger = setup_logger('fisher_input')

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
        
        logger.info("输入控制器初始化完成 - 使用Windows mouse_event API游戏兼容模式")
    
    def _move_mouse_windows_api(self, dx: int, dy: int) -> bool:
        """
        使用Windows mouse_event API移动鼠标（游戏兼容，直接像素移动）
        
        Args:
            dx: X轴移动距离（像素）
            dy: Y轴移动距离（像素）
            
        Returns:
            bool: 是否成功移动
        """
        try:
            # 使用mouse_event API（最兼容游戏锁定）
            MOUSEEVENTF_MOVE = 0x0001
            result = ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVE, dx, dy, 0, 0)
            logger.debug(f"Windows mouse_event API移动: dx={dx}, dy={dy}")
            return True
            
        except Exception as e:
            logger.error(f"Windows API移动失败: {e}")
            return False
    
    def move_mouse(self, direction: str = "right", distance_pixels: Optional[int] = None) -> bool:
        """
        使用Windows mouse_event API移动鼠标（游戏兼容，直接像素移动）
        
        Args:
            direction: 移动方向，支持8个方向:
                      - 基本方向: "right", "left", "up", "down"
                      - 对角线方向: "right-down", "right-up", "left-down", "left-up"
            distance_pixels: 移动距离（像素），None表示使用配置文件的默认值
            
        Returns:
            bool: 是否成功移动
        """
        try:
            # 获取配置的移动距离（像素）
            if distance_pixels is None:
                distance_pixels = fisher_config.retry.mouse_move_pixels
            
            logger.info(f"开始鼠标{direction}移动，距离: {distance_pixels}px")
            
            # 如果距离为0或负数，跳过移动
            if distance_pixels <= 0:
                logger.warning(f"移动距离无效: {distance_pixels}px，跳过移动")
                return True
            
            # 根据方向计算移动向量
            direction_vectors = {
                "right": (distance_pixels, 0),      # 向右：X轴正方向
                "left": (-distance_pixels, 0),      # 向左：X轴负方向
                "down": (0, distance_pixels),       # 向下：Y轴正方向
                "up": (0, -distance_pixels),        # 向上：Y轴负方向
                # 对角线移动（使用勾股定理保持总距离不变）
                "right-down": (int(distance_pixels * 0.707), int(distance_pixels * 0.707)),    # 向右下：45度角
                "right-up": (int(distance_pixels * 0.707), int(-distance_pixels * 0.707)),     # 向右上：-45度角
                "left-down": (int(-distance_pixels * 0.707), int(distance_pixels * 0.707)),    # 向左下：135度角
                "left-up": (int(-distance_pixels * 0.707), int(-distance_pixels * 0.707))      # 向左上：-135度角
            }
            
            if direction not in direction_vectors:
                logger.error(f"不支持的移动方向: {direction}，支持的方向: {list(direction_vectors.keys())}")
                return False
            
            dx, dy = direction_vectors[direction]
            logger.info(f"计算移动向量: {direction} → dx={dx}, dy={dy}")
            
            # 使用Windows mouse_event API移动鼠标
            success = self._move_mouse_windows_api(dx, dy)
            
            if success:
                # 等待移动完成
                move_delay = fisher_config.retry.mouse_move_delay
                time.sleep(move_delay)
                
                logger.info(f"🖱️  鼠标{direction}移动成功 (Windows API): {distance_pixels}px → dx={dx}, dy={dy}")
                return True
            else:
                logger.error(f"Windows API鼠标移动失败，方向: {direction}, 距离: {distance_pixels}px")
                return False
            
        except Exception as e:
            logger.error(f"鼠标{direction}移动失败: {e}")
            return False
    
    def move_mouse_right(self, distance_pixels: Optional[int] = None) -> bool:
        """
        向右移动鼠标(保持向后兼容性)
        
        Args:
            distance_pixels: 移动距离（像素）
            
        Returns:
            bool: 是否成功移动
        """
        return self.move_mouse("right", distance_pixels)
    
    def _click_worker(self) -> None:
        """
        鼠标点击工作线程
        持续执行鼠标点击，直到收到停止信号
        """
        logger.info("鼠标点击线程启动")
        
        while not self.stop_clicking_event.is_set():
            # 等待点击信号
            if self.click_event.wait(timeout=0.1):
                # 执行点击
                try:
                    # 生成随机时间参数
                    press_time = random.uniform(
                        fisher_config.timing.mouse_press_time_min,
                        fisher_config.timing.mouse_press_time_max
                    )
                    release_time = random.uniform(
                        fisher_config.timing.mouse_release_time_min,
                        fisher_config.timing.mouse_release_time_max
                    )
                    click_interval = random.uniform(
                        fisher_config.timing.click_interval_min,
                        fisher_config.timing.click_interval_max
                    )
                    
                    # 鼠标左键按下
                    pyautogui.mouseDown(button='left')
                    time.sleep(press_time)  # 按下持续时间
                    
                    # 鼠标左键弹起
                    pyautogui.mouseUp(button='left')
                    time.sleep(release_time)  # 弹起后短暂等待
                    
                    # 等待下次点击间隔
                    time.sleep(click_interval)
                    
                    # 每100次点击输出一次时间统计（调试用）
                    if hasattr(self, '_click_count'):
                        self._click_count += 1
                    else:
                        self._click_count = 1
                        
                    if self._click_count % 100 == 0:
                        logger.debug(f"🖱️  点击统计: 按下{press_time:.3f}s, 弹起等待{release_time:.3f}s, 间隔{click_interval:.3f}s")
                    
                except Exception as e:
                    logger.error(f"鼠标点击失败: {e}")
                    break
            
            # 检查是否暂停点击
            if not self.click_running.is_set():
                self.click_event.clear()
        
        logger.info("鼠标点击线程结束")
    
    def start_clicking(self) -> bool:
        """
        开始快速点击
        
        Returns:
            bool: 是否成功启动
        """
        try:
            if self.click_thread and self.click_thread.is_alive():
                logger.info("点击线程已在运行")
                return True
            
            # 重置停止信号
            self.stop_clicking_event.clear()
            
            # 创建并启动点击线程
            self.click_thread = threading.Thread(target=self._click_worker, daemon=True)
            self.click_thread.start()
            
            # 启动点击
            self.click_running.set()
            self.click_event.set()
            
            logger.info("快速点击已启动")
            return True
            
        except Exception as e:
            logger.error(f"启动点击失败: {e}")
            return False
    
    def pause_clicking(self) -> None:
        """暂停点击"""
        self.click_running.clear()
        self.click_event.clear()
        logger.info("鼠标点击已暂停")
    
    def resume_clicking(self) -> None:
        """恢复点击"""
        if self.click_thread and self.click_thread.is_alive():
            self.click_running.set()
            self.click_event.set()
            logger.info("鼠标点击已恢复")
        else:
            logger.info("点击线程未运行，尝试重新启动")
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
            
            logger.info("快速点击已停止")
            
        except Exception as e:
            logger.error(f"停止点击失败: {e}")
    
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
            
            logger.info(f"按键 '{key}' 持续 {duration:.2f}秒")
            return True
            
        except Exception as e:
            logger.error(f"按键 '{key}' 失败: {e}")
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
            logger.error(f"启动按键线程失败: {e}")
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
            
            logger.info(f"鼠标左键点击 ({x}, {y})")
            return True
            
        except Exception as e:
            logger.error(f"鼠标点击失败: {e}")
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
            
            logger.info(f"鼠标左键长按 {duration:.2f}秒")
            return True
            
        except Exception as e:
            logger.error(f"鼠标长按失败: {e}")
            return False
    
    def handle_direction_key(self, direction_state: int) -> bool:
        """
        根据方向状态按下对应按键
        
        注意：此方法已废弃，新模型中不再使用状态4和5的方向检测
        
        Args:
            direction_state: 方向状态 (已废弃)
            
        Returns:
            bool: 总是返回False（已废弃）
        """
        logger.warning(f"handle_direction_key已废弃，状态{direction_state}不再支持")
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
            logger.error(f"处理成功状态失败: {e}")
            return False
    
    def cast_rod(self) -> bool:
        """
        抛竿操作（长按鼠标左键2秒）
        
        Returns:
            bool: 是否成功抛竿
        """
        logger.info("执行抛竿操作")
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
        logger.warning("紧急停止所有输入操作")
        
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
        logger.info("清理输入控制器资源")
        self.emergency_stop()

# 全局输入控制器实例
input_controller = InputController() 