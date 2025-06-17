#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AutoFish钓鱼控制器模块 v2.4.1

实现钓鱼的核心状态机和流程控制逻辑。
采用三线程架构：
1. 主线程：状态识别和线程控制
2. 鼠标点击线程：独立快速点击
3. OCR识别线程：独立OCR识别和方向按键
"""

import time
import logging
import threading
from enum import Enum
from typing import Optional, Callable, Dict

from modules.auto_fisher.config import get_config
from modules.auto_fisher.state_detector import get_detector
from modules.auto_fisher.input_controller import get_input_controller
from modules.auto_fisher.hotkey_manager import get_hotkey_manager


class FishingState(Enum):
    """钓鱼状态枚举"""
    IDLE = -1              # 空闲状态
    WAITING = 0            # 等待上钩状态
    FISH_HOOKED = 1        # 鱼上钩末提线状态
    PULLING_NORMAL = 2     # 提线中_耐力未到二分之一状态
    PULLING_HALFWAY = 3    # 提线中_耐力已到二分之一状态
    PULL_RIGHT = 4         # 向右拉_txt
    PULL_LEFT = 5          # 向左拉_txt
    SUCCESS = 6            # 钓鱼成功状态_txt


class FishingController:
    """钓鱼控制器类 - 三线程架构"""
    
    def __init__(self):
        """初始化钓鱼控制器"""
        self.config = get_config()
        self.detector = get_detector()
        self.input_controller = get_input_controller()
        self.hotkey_manager = get_hotkey_manager()
        
        # 当前状态
        self.current_state = FishingState.IDLE
        self.previous_state = None
        
        # 主线程控制
        self.is_running = False
        self.is_paused = False
        self.main_thread: Optional[threading.Thread] = None
        
        # 鼠标点击线程控制
        self.click_thread: Optional[threading.Thread] = None
        self.click_active = False
        self.click_lock = threading.Lock()
        
        # OCR识别线程控制
        self.ocr_thread: Optional[threading.Thread] = None
        self.ocr_active = False
        self.ocr_lock = threading.Lock()
        
        # 状态切换时间记录
        self.state_start_time = time.time()
        self.max_wait_time = self.config.get('fishing.max_wait_time', 180)
        
        # 状态回调函数
        self.state_callback: Optional[Callable[[FishingState], None]] = None
        
        # 设置热键回调
        self.hotkey_manager.set_callbacks(
            start_callback=self._hotkey_start,
            stop_callback=self._hotkey_stop,
            pause_callback=self._hotkey_pause
        )
        
        logging.info("钓鱼控制器初始化完成 - 三线程架构")
    
    def set_state_callback(self, callback: Callable[[FishingState], None]):
        """设置状态变化回调函数"""
        self.state_callback = callback
    
    def start(self):
        """开始钓鱼"""
        if self.is_running:
            logging.warning("钓鱼程序已在运行")
            return
        
        self.is_running = True
        self.is_paused = False
        
        # 启动热键监听
        self.hotkey_manager.start_listening()
        
        self.main_thread = threading.Thread(target=self._main_loop, daemon=True)
        self.main_thread.start()
        logging.info("开始钓鱼程序 - 三线程架构")
    
    def stop(self):
        """停止钓鱼"""
        if not self.is_running:
            return
        
        self.is_running = False
        self.is_paused = False
        
        # 停止所有线程
        self._stop_click_thread()
        self._stop_ocr_thread()
        
        # 停止热键监听
        self.hotkey_manager.stop_listening()
        
        # 清理资源
        self.input_controller.cleanup()
        
        # 等待主线程结束
        if self.main_thread and self.main_thread.is_alive():
            self.main_thread.join(timeout=2.0)
        
        # 切换到空闲状态
        self._change_state(FishingState.IDLE)
        
        logging.info("停止钓鱼程序")
    
    def pause(self):
        """暂停钓鱼"""
        if self.is_running and not self.is_paused:
            self.is_paused = True
            # 暂停时停止所有子线程
            self._stop_click_thread()
            self._stop_ocr_thread()
            logging.info("暂停钓鱼程序")
    
    def resume(self):
        """恢复钓鱼"""
        if self.is_running and self.is_paused:
            self.is_paused = False
            logging.info("恢复钓鱼程序")
    
    def _main_loop(self):
        """主线程循环 - 只负责状态识别和线程控制"""
        try:
            # 初始状态检测
            self._wait_for_fishing_state()
            
            while self.is_running:
                if self.is_paused:
                    time.sleep(0.1)
                    continue
                
                # 检测状态
                detections = self.detector.detect_states()
                
                # 处理状态识别和线程控制
                self._process_state_and_control_threads(detections)
                
                # 检查超时
                self._check_timeout()
                
                # 根据当前状态获取动态检测间隔
                interval = self._get_current_detection_interval()
                time.sleep(interval)
                
        except Exception as e:
            logging.error(f"钓鱼主循环出错: {e}")
            import traceback
            logging.error(traceback.format_exc())
        finally:
            self._cleanup()
    
    def _wait_for_fishing_state(self):
        """等待进入钓鱼状态"""
        logging.info("等待进入钓鱼状态...")
        
        timeout = 30  # 30秒超时
        start_time = time.time()
        
        while self.is_running and not self.is_paused:
            if time.time() - start_time > timeout:
                logging.error("等待钓鱼状态超时")
                self.stop()
                return
            
            detections = self.detector.detect_states()
            
            # 检测到状态0或1都可以开始
            if 0 in detections or 1 in detections:
                if 0 in detections:
                    self._change_state(FishingState.WAITING)
                else:
                    self._change_state(FishingState.FISH_HOOKED)
                    # 状态1时启动鼠标点击线程和OCR线程
                    self._start_click_thread()
                    self._start_ocr_thread()
                logging.info("成功进入钓鱼状态")
                return
            
            time.sleep(0.2)
    
    def _process_state_and_control_threads(self, detections: Dict[int, float]):
        """
        处理状态识别并控制线程
        
        Args:
            detections: 检测结果字典
        """
        if not detections:
            return
        
        # 获取置信度最高的状态
        best_detection = self.detector.get_highest_confidence_state(detections)
        if not best_detection:
            return
        
        state_id, confidence = best_detection
        new_state = None
        
        # 状态映射
        if state_id == 0:
            new_state = FishingState.WAITING
        elif state_id == 1:
            new_state = FishingState.FISH_HOOKED
        elif state_id == 2:
            new_state = FishingState.PULLING_NORMAL
        elif state_id == 3:
            new_state = FishingState.PULLING_HALFWAY
        elif state_id == 6:
            new_state = FishingState.SUCCESS
        
        if new_state and new_state != self.current_state:
            self._handle_state_transition(new_state)
    
    def _handle_state_transition(self, new_state: FishingState):
        """
        处理状态转换和线程控制
        
        Args:
            new_state: 新状态
        """
        old_state = self.current_state
        self._change_state(new_state)
        
        # 根据状态转换控制线程
        if new_state == FishingState.WAITING:
            # 进入等待状态，停止所有线程
            self._stop_click_thread()
            self._stop_ocr_thread()
            
        elif new_state == FishingState.FISH_HOOKED:
            # 进入鱼上钩状态，启动点击线程和OCR线程
            self._start_click_thread()
            self._start_ocr_thread()
            
        elif new_state == FishingState.PULLING_NORMAL:
            # 进入提线普通状态，启动点击线程
            self._start_click_thread()
            # OCR线程保持运行
            
        elif new_state == FishingState.PULLING_HALFWAY:
            # 进入提线一半状态，停止点击线程
            self._stop_click_thread()
            # OCR线程保持运行
            
        elif new_state == FishingState.SUCCESS:
            # 进入成功状态，停止所有线程
            self._stop_click_thread()
            self._stop_ocr_thread()
            # 执行成功后的操作
            self._handle_success_actions()
    
    def _handle_success_actions(self):
        """处理钓鱼成功后的动作"""
        logging.info("钓鱼成功，执行后续动作")
        
        # 等待1.5秒后按F键
        time.sleep(self.config.get('fishing.success_wait_time', 1.5))
        self.input_controller.confirm_action()
        
        # 检查是否还在成功状态
        time.sleep(0.5)
        detections = self.detector.detect_states()
        
        if 6 in detections:
            # 仍在成功状态，继续等待
            time.sleep(1.0)
        else:
            # 成功状态结束，抛竿进入下一轮
            self._cast_and_restart()
    
    def _cast_and_restart(self):
        """抛竿并重新开始"""
        logging.info("抛竿进入下一轮钓鱼")
        
        # 确保所有线程已停止
        self._stop_click_thread()
        self._stop_ocr_thread()
        
        # 释放所有按键
        self.input_controller.release_all_keys()
        
        # 抛竿
        self.input_controller.cast_fishing_rod()
        
        # 等待一下然后重新开始检测
        time.sleep(1.0)
        self._change_state(FishingState.WAITING)
        self.state_start_time = time.time()
    
    def _start_click_thread(self):
        """启动鼠标点击线程"""
        with self.click_lock:
            if self.click_active:
                return
            
            self.click_active = True
            self.click_thread = threading.Thread(target=self._click_worker, daemon=True)
            self.click_thread.start()
            logging.debug("启动鼠标点击线程")
    
    def _stop_click_thread(self):
        """停止鼠标点击线程"""
        with self.click_lock:
            if not self.click_active:
                return
            
            self.click_active = False
            if self.click_thread and self.click_thread.is_alive():
                self.click_thread.join(timeout=1.0)
            logging.debug("停止鼠标点击线程")
    
    def _click_worker(self):
        """鼠标点击工作线程"""
        min_interval = self.config.get('fishing.click_interval_min', 0.054)
        max_interval = self.config.get('fishing.click_interval_max', 0.127)
        
        while self.click_active and self.is_running and not self.is_paused:
            try:
                # 随机点击间隔
                import random
                press_time = random.uniform(min_interval, max_interval)
                release_time = random.uniform(min_interval, max_interval)
                
                # 使用PyAutoGUI直接控制鼠标
                import pyautogui
                pyautogui.mouseDown()
                time.sleep(press_time)
                pyautogui.mouseUp()
                time.sleep(release_time)
                
            except pyautogui.FailSafeException:
                logging.warning("检测到Fail-Safe触发 - 鼠标移动到左上角，紧急停止程序")
                # 触发主程序停止
                if self.is_running:
                    threading.Thread(target=self.stop, daemon=True).start()
                break
            except Exception as e:
                logging.error(f"鼠标点击线程出错: {e}")
                break
    
    def _start_ocr_thread(self):
        """启动OCR识别线程"""
        with self.ocr_lock:
            if self.ocr_active:
                return
            
            self.ocr_active = True
            self.ocr_thread = threading.Thread(target=self._ocr_worker, daemon=True)
            self.ocr_thread.start()
            logging.debug("启动OCR识别线程")
    
    def _stop_ocr_thread(self):
        """停止OCR识别线程"""
        with self.ocr_lock:
            if not self.ocr_active:
                return
            
            self.ocr_active = False
            # 释放方向按键
            self.input_controller.release_all_keys()
            if self.ocr_thread and self.ocr_thread.is_alive():
                self.ocr_thread.join(timeout=1.0)
            logging.debug("停止OCR识别线程")
    
    def _ocr_worker(self):
        """OCR识别工作线程"""
        while self.ocr_active and self.is_running and not self.is_paused:
            try:
                # OCR检测
                image = self.detector.capture_screen()
                if image is not None:
                    ocr_detections = self.detector.detect_ocr_states(image)
                    
                    # 处理方向状态
                    if 4 in ocr_detections:  # 向右拉
                        self.input_controller.handle_direction_key('right')
                    elif 5 in ocr_detections:  # 向左拉
                        self.input_controller.handle_direction_key('left')
                    else:
                        # 没有方向指示，释放按键
                        self.input_controller.release_all_keys()
                
                # 根据当前状态获取动态OCR检测间隔
                ocr_interval = self._get_current_ocr_detection_interval()
                time.sleep(ocr_interval)
                
            except Exception as e:
                logging.error(f"OCR识别线程出错: {e}")
                break
    
    def _check_timeout(self):
        """检查超时"""
        if self.current_state in [FishingState.WAITING, FishingState.FISH_HOOKED]:
            elapsed_time = time.time() - self.state_start_time
            if elapsed_time > self.max_wait_time:
                logging.warning(f"状态 {self.current_state.name} 超时，自动结束钓鱼")
                self.stop()
    
    def _change_state(self, new_state: FishingState):
        """
        改变状态
        
        Args:
            new_state: 新状态
        """
        if self.current_state == new_state:
            return
        
        self.previous_state = self.current_state
        self.current_state = new_state
        self.state_start_time = time.time()
        
        # 调用回调函数
        if self.state_callback:
            try:
                self.state_callback(new_state)
            except Exception as e:
                logging.error(f"状态回调函数出错: {e}")
        
        # 记录状态变化
        state_name = self.detector.get_state_name(new_state.value) if new_state.value >= 0 else new_state.name
        logging.info(f"状态变化: {self.previous_state} -> {new_state.name} ({state_name})")
    
    def _get_current_detection_interval(self) -> float:
        """
        获取当前状态的检测间隔
        
        Returns:
            检测间隔秒数
        """
        state_map = {
            FishingState.IDLE: "idle",
            FishingState.WAITING: "waiting", 
            FishingState.FISH_HOOKED: "fish_hooked",
            FishingState.PULLING_NORMAL: "pulling",
            FishingState.PULLING_HALFWAY: "pulling",
            FishingState.PULL_RIGHT: "pulling",
            FishingState.PULL_LEFT: "pulling",
            FishingState.SUCCESS: "success"
        }
        
        state_type = state_map.get(self.current_state, "default")
        return self.config.get_detection_interval(state_type)
    
    def _get_current_ocr_detection_interval(self) -> float:
        """
        获取当前状态的OCR检测间隔
        
        Returns:
            OCR检测间隔秒数
        """
        if self.current_state == FishingState.PULLING_NORMAL:
            return self.config.get_ocr_detection_interval("pulling_normal")
        elif self.current_state == FishingState.PULLING_HALFWAY:
            return self.config.get_ocr_detection_interval("pulling_halfway")
        else:
            return self.config.get_ocr_detection_interval("default")
    
    def _hotkey_start(self):
        """热键开始钓鱼"""
        if not self.is_running:
            self.start()
        elif self.is_paused:
            self.resume()
    
    def _hotkey_stop(self):
        """热键停止钓鱼"""
        if self.is_running:
            self.stop()
    
    def _hotkey_pause(self):
        """热键暂停/恢复钓鱼"""
        if self.is_running:
            if self.is_paused:
                self.resume()
            else:
                self.pause()
    
    def _cleanup(self):
        """清理资源"""
        self._stop_click_thread()
        self._stop_ocr_thread()
        self.input_controller.cleanup()
    
    def get_current_state(self) -> FishingState:
        """获取当前状态"""
        return self.current_state
    
    def is_active(self) -> bool:
        """检查是否活跃"""
        return self.is_running and not self.is_paused
    
    def get_thread_status(self) -> Dict[str, bool]:
        """获取线程状态"""
        return {
            "main": self.is_running and not self.is_paused,
            "click": self.click_active,
            "ocr": self.ocr_active
        }


# 全局钓鱼控制器实例
_fishing_controller_instance: Optional[FishingController] = None


def get_fishing_controller() -> FishingController:
    """获取钓鱼控制器实例"""
    global _fishing_controller_instance
    if _fishing_controller_instance is None:
        _fishing_controller_instance = FishingController()
    return _fishing_controller_instance 