#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
钓鱼状态机模块

该模块实现钓鱼过程的状态机逻辑，控制整个钓鱼流程的自动化。
"""

import time
import logging
import threading
import random
from enum import Enum
from typing import Optional, Dict, List, Tuple, Callable
import pyautogui

# 导入相关模块
from modules.auto_fisher.model_detector import get_instance as get_model_detector
from modules.auto_fisher.input_simulator import get_instance as get_input_simulator
from modules.auto_fisher.config_manager import get_instance as get_config_manager
from modules.auto_fisher.ocr_processor import get_instance as get_ocr_processor
from modules.auto_fisher.key_controller import get_instance as get_key_controller


class FishingState(Enum):
    """钓鱼状态枚举"""
    INITIALIZING = -2      # 初始化状态
    IDLE = -1              # 空闲状态
    WAITING_FOR_FISH = 0   # 等待上钩状态
    FISH_DETECTED = 1      # 鱼上钩未提线状态
    PULLING_NORMAL = 2     # 提线中_耐力未到二分之一状态
    PULLING_HALFWAY = 3    # 提线中_耐力已到二分之一状态
    PULL_RIGHT = 4         # 向右拉_txt
    PULL_LEFT = 5          # 向左拉_txt
    SUCCESS = 6            # 钓鱼成功状态_txt


class FishingStateMachine:
    """
    钓鱼状态机类
    
    实现钓鱼自动化的核心状态机逻辑。
    """
    
    def __init__(self):
        """
        初始化钓鱼状态机
        """
        # 获取相关模块实例
        self.detector = get_model_detector()
        self.simulator = get_input_simulator()
        self.config = get_config_manager()
        self.ocr_processor = get_ocr_processor()
        self.key_controller = get_key_controller()
        
        # 获取配置值
        self.wait_times = self.config.get_wait_times()
        
        # 当前状态
        self.current_state = FishingState.INITIALIZING
        
        # 上一个状态
        self.previous_state = None
        
        # 状态转换时间记录
        self.state_change_time = time.time()
        
        # 运行标志
        self.is_running = False
        self.is_paused = False
        
        # 工作线程
        self.thread = None
        
        # 点击控制相关变量
        self.clicking_thread = None
        self.stop_clicking = True
        
        # 方向操作标志
        self.direction_active = False
        
        # 状态回调函数（用于UI更新）
        self.state_callback: Optional[Callable[[FishingState], None]] = None
        
        # 调试标志
        self.debug_mode = False
        
        # OCR状态
        self.ocr_active = False
        
        # 设置OCR回调函数
        self.ocr_processor.set_direction_callback(self._handle_ocr_direction)
        
        # 状态耗时统计
        self.state_durations: Dict[FishingState, float] = {}
        for state in FishingState:
            self.state_durations[state] = 0.0
            
        # 日志记录时间
        self.last_log_time = time.time()
        
        # 自动抛竿标志
        self.auto_cast = True
        
        # 抛竿键
        self.cast_key = 'left'  # 默认使用鼠标左键抛竿
        
        # 状态检测计数器
        self.state_detection_counters = {state: 0 for state in FishingState}
        
        # 状态检测阈值（连续检测到几次才确认状态变化）
        self.state_detection_threshold = 2
        
        logging.info("钓鱼状态机初始化完成")
    
    def set_state_callback(self, callback: Callable[[FishingState], None]):
        """
        设置状态变化回调函数
        
        Args:
            callback: 状态变化回调函数
        """
        self.state_callback = callback
    
    def _change_state(self, new_state: FishingState):
        """
        更改当前状态
        
        Args:
            new_state: 新状态
        """
        # 记录状态持续时间
        current_time = time.time()
        duration = current_time - self.state_change_time
        self.state_durations[self.current_state] += duration
        
        # 更新状态
        self.previous_state = self.current_state
        self.current_state = new_state
        self.state_change_time = current_time
        
        # 调用回调函数
        if self.state_callback:
            try:
                logging.info(f"调用状态回调函数: {self.previous_state.name} -> {new_state.name}")
                self.state_callback(new_state)
            except Exception as e:
                logging.error(f"执行状态回调函数时出错: {str(e)}")
                import traceback
                logging.error(traceback.format_exc())
        
        # 记录日志
        logging.info(f"状态变化: {self.previous_state.name} -> {self.current_state.name}")
        
        # 根据状态控制OCR识别
        self._manage_ocr_state(new_state)
        
        # 重置状态检测计数器
        for state in FishingState:
            self.state_detection_counters[state] = 0
    
    def _manage_ocr_state(self, state: FishingState):
        """
        根据状态管理OCR识别
        
        Args:
            state: 当前状态
        """
        # 在状态2或3时启动OCR识别
        if state in [FishingState.PULLING_NORMAL, FishingState.PULLING_HALFWAY] and not self.ocr_active:
            logging.info("进入提线状态，启动OCR文字识别")
            self.ocr_active = True
            if hasattr(self.ocr_processor, 'is_running') and self.ocr_processor.is_running:
                self.ocr_processor.resume()
            else:
                self.ocr_processor.start()
        
        # 在状态6时停止OCR识别
        elif state == FishingState.SUCCESS and self.ocr_active:
            logging.info("进入成功状态，停止OCR文字识别")
            self.ocr_active = False
            if hasattr(self.ocr_processor, 'pause'):
                self.ocr_processor.pause()
            # 释放可能按下的按键
            self.key_controller.release_key()
    
    def _handle_ocr_direction(self, direction: str):
        """
        处理OCR识别到的方向
        
        Args:
            direction: 方向('left'或'right')
        """
        if not self.ocr_active:
            return
            
        if direction == "left":
            logging.info("OCR识别到向左拉，按下A键")
            self.key_controller.handle_direction("left")
        elif direction == "right":
            logging.info("OCR识别到向右拉，按下D键")
            self.key_controller.handle_direction("right")
    
    def start(self):
        """
        启动钓鱼状态机
        """
        if self.is_running:
            logging.warning("钓鱼状态机已在运行中")
            return
        
        # 重置状态
        self._change_state(FishingState.IDLE)
        self.is_running = True
        self.is_paused = False
        
        # 重置状态耗时统计
        for state in FishingState:
            self.state_durations[state] = 0.0
        
        # 启动工作线程
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        
        logging.info("钓鱼状态机已启动")
    
    def stop(self):
        """
        停止状态机
        """
        if not self.is_running:
            return
        
        logging.info("正在停止钓鱼状态机...")
        
        # 设置停止标志
        self.is_running = False
        
        # 停止快速点击
        self._stop_rapid_clicking()
        
        # 等待线程结束
        if hasattr(self, 'thread') and self.thread and self.thread.is_alive():
            # 避免尝试加入当前线程
            if self.thread != threading.current_thread():
                try:
                    self.thread.join(timeout=3)
                except RuntimeError as e:
                    logging.warning(f"无法加入线程: {str(e)}")
        
        # 重置状态
        self._change_state(FishingState.IDLE)
        
        # 重置检测计数器
        self._reset_detection_counters()
        
        logging.info("钓鱼状态机已停止")
    
    def pause(self):
        """
        暂停钓鱼状态机
        """
        if self.is_running and not self.is_paused:
            self.is_paused = True
            
            # 暂停OCR识别
            if self.ocr_active and hasattr(self.ocr_processor, 'pause'):
                self.ocr_processor.pause()
                
            # 释放按键
            self.key_controller.release_key()
            
            logging.info("钓鱼状态机已暂停")
    
    def resume(self):
        """
        恢复钓鱼状态机
        """
        if self.is_running and self.is_paused:
            self.is_paused = False
            
            # 恢复OCR识别
            if self.ocr_active and hasattr(self.ocr_processor, 'resume'):
                self.ocr_processor.resume()
                
            logging.info("钓鱼状态机已恢复")
    
    def is_active(self) -> bool:
        """
        检查状态机是否处于活动状态
        
        Returns:
            是否活动
        """
        return self.is_running and not self.is_paused
    
    def _run(self):
        """
        状态机主循环
        """
        try:
            logging.info("钓鱼状态机主循环启动")
            
            while self.is_running:
                # 如果暂停，则等待
                if self.is_paused:
                    time.sleep(0.1)
                    continue
                
                # 获取当前检测到的状态
                detected_states = self.detector.get_current_state()
                
                # 处理当前状态
                self._process_state(detected_states)
                
                # 根据当前状态调整检测频率
                if self.current_state == FishingState.WAITING_FOR_FISH:
                    # 等待上钩状态 - 较低频率检测
                    time.sleep(0.3)
                elif self.current_state in [FishingState.FISH_DETECTED, FishingState.PULLING_NORMAL]:
                    # 鱼上钩和提线状态 - 高频率检测
                    time.sleep(0.1)
                elif self.current_state == FishingState.PULLING_HALFWAY:
                    # 耐力过半状态 - 中等频率检测
                    time.sleep(0.2)
                else:
                    # 其他状态 - 默认频率
                    time.sleep(1.0 / self.config.get_model_fps())
                
                # 记录当前状态（每5秒记录一次）
                current_time = time.time()
                if not hasattr(self, 'last_log_time') or current_time - self.last_log_time > 5:
                    logging.info(f"当前状态: {self.current_state.name}")
                    self.last_log_time = current_time
                    
        except Exception as e:
            logging.error(f"钓鱼状态机运行出错: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            self.stop()
    
    def _process_state(self, detected_states: Dict[int, float]):
        """
        处理当前检测到的状态
        
        Args:
            detected_states: 检测到的状态ID和置信度字典
        """
        # 如果调试模式开启，输出检测状态
        if detected_states and self.debug_mode:
            states_str = ", ".join([f"{self.detector.get_state_name(state_id)}({conf:.2f})" 
                                   for state_id, conf in detected_states.items()])
            logging.debug(f"检测到的状态: {states_str}")
        
        # 如果没有检测到任何状态
        if not detected_states:
            # 如果当前正在钓鱼成功状态，但未检测到该状态，则可能钓鱼成功状态已消失
            if self.current_state == FishingState.SUCCESS:
                logging.info("钓鱼成功状态消失，准备开始新一轮钓鱼")
                self.simulator.mouse_long_press('left')
                self._reset_to_waiting_state()
            return
        
        # 使用状态检测计数器来确保状态稳定性
        for state_id, confidence in detected_states.items():
            if state_id in [s.value for s in FishingState]:
                self.state_detection_counters[FishingState(state_id)] += 1
        
        # 衰减未检测到的状态计数器
        for state in FishingState:
            if state.value not in detected_states:
                self.state_detection_counters[state] = max(0, self.state_detection_counters[state] - 1)
        
        # 获取最稳定的状态（连续检测次数最多的状态）
        stable_states = {state: count for state, count in self.state_detection_counters.items() 
                        if count >= self.state_detection_threshold and state.value in detected_states}
        
        # 记录当前检测到的稳定状态，便于调试
        if stable_states:
            stable_states_str = ", ".join([f"{state.name}({count})" for state, count in stable_states.items()])
            logging.debug(f"稳定状态: {stable_states_str}")
        
        # 按照状态优先级处理
        
        # 1. 首先检查是否为钓鱼成功状态（最高优先级）
        if FishingState.SUCCESS in stable_states and self.current_state != FishingState.SUCCESS:
            logging.info("检测到钓鱼成功状态")
            self._stop_rapid_clicking()  # 停止快速点击
            self._change_state(FishingState.SUCCESS)
            # 等待指定时间
            time.sleep(self.wait_times['state_6_wait'])
            # 按下F键
            self.simulator.key_press('f')
            logging.info("钓鱼成功，按下F键")
            return
        elif self.current_state == FishingState.SUCCESS and FishingState.SUCCESS.value in detected_states:
            # 如果当前已经是成功状态，且仍然检测到成功状态，继续按F键
            time.sleep(self.wait_times['state_6_wait'])
            self.simulator.key_press('f')
            logging.info("钓鱼成功状态持续，再次按下F键")
            return
        
        # 2. 检查是否为耐力过半状态（第二优先级）
        if FishingState.PULLING_HALFWAY in stable_states:
            if self.current_state != FishingState.PULLING_HALFWAY:
                logging.info("检测到耐力过半状态，停止快速点击")
                self._stop_rapid_clicking()  # 停止快速点击
                self._change_state(FishingState.PULLING_HALFWAY)
                # 等待一秒
                time.sleep(self.wait_times['state_3_pause'])
                logging.info(f"等待 {self.wait_times['state_3_pause']} 秒后继续检测状态")
            return
        
        # 3. 检查是否为提线中状态（第三优先级）
        if FishingState.PULLING_NORMAL in stable_states:
            # 如果当前是耐力过半状态，但检测到普通提线状态，则恢复快速点击
            if self.current_state == FishingState.PULLING_HALFWAY:
                logging.info("从耐力过半返回普通提线状态，恢复快速点击")
                self._start_rapid_clicking()
                self._change_state(FishingState.PULLING_NORMAL)
                return
            # 如果当前是鱼上钩状态，则转为提线中状态
            elif self.current_state == FishingState.FISH_DETECTED:
                logging.info("从鱼上钩转为提线中状态")
                self._change_state(FishingState.PULLING_NORMAL)
                # 继续保持快速点击
                return
            # 如果当前已经是提线中状态，不做任何改变
            elif self.current_state == FishingState.PULLING_NORMAL:
                # 不做任何改变，但继续处理后续状态
                pass
            else:
                # 其他状态转为提线中状态
                logging.info(f"从{self.current_state.name}转为提线中状态")
                self._change_state(FishingState.PULLING_NORMAL)
                return
        
        # 4. 检查是否为鱼上钩状态（第四优先级）
        if FishingState.FISH_DETECTED in stable_states:
            # 允许从IDLE状态或WAITING_FOR_FISH状态转为鱼上钩状态
            if self.current_state in [FishingState.WAITING_FOR_FISH, FishingState.IDLE]:
                logging.info(f"检测到鱼上钩，当前状态: {self.current_state.name}，开始快速点击")
                self._start_rapid_clicking()  # 开始快速点击
                self._change_state(FishingState.FISH_DETECTED)
                return
        
        # 5. 检查是否为等待上钩状态（最低优先级）
        if FishingState.WAITING_FOR_FISH in stable_states:
            # 单进程状态：只有当前是空闲状态时，才转为等待上钩状态
            if self.current_state == FishingState.IDLE:
                logging.info("检测到等待上钩状态")
                self._change_state(FishingState.WAITING_FOR_FISH)
                return
        
        # 处理方向键状态 - 注意：主要由OCR处理器处理
        # 这里作为备份方案，当OCR识别失败时使用
        if self.current_state in [FishingState.PULLING_NORMAL, FishingState.PULLING_HALFWAY]:
            if FishingState.PULL_RIGHT.value in detected_states or FishingState.PULL_LEFT.value in detected_states:
                self._process_direction_states(detected_states)
    
    def _reset_to_waiting_state(self):
        """
        重置为等待上钩状态，准备开始新一轮钓鱼
        """
        # 设置定时器，如果在指定时间内没有检测到等待上钩状态，则结束钓鱼
        start_time = time.time()
        self._change_state(FishingState.IDLE)
        
        # 等待检测到等待上钩状态或超时
        while self.is_running and not self.is_paused:
            detected_states = self.detector.get_current_state()
            
            # 检查是否检测到等待上钩状态
            if FishingState.WAITING_FOR_FISH.value in detected_states:
                self._change_state(FishingState.WAITING_FOR_FISH)
                return
            
            # 检查是否超时
            if time.time() - start_time > self.wait_times['state_0_timeout']:
                logging.info("等待上钩状态超时，钓鱼可能已结束")
                self.stop()
                return
            
            # 短暂休眠
            time.sleep(0.1)
    
    def _process_direction_states(self, detected_states: Dict[int, float]):
        """
        处理方向键状态（左/右拉）
        
        注意: 此方法已主要被OCR处理器取代，但保留为后备方案，
        当OCR识别失败时，仍可通过YOLO模型检测到的方向状态来执行按键操作。
        
        Args:
            detected_states: 检测到的状态ID和置信度字典
        """
        # 检测到向右拉状态
        if FishingState.PULL_RIGHT.value in detected_states:
            # 标记方向操作激活
            was_direction_active = self.direction_active
            self.direction_active = True
            
            # 首次激活方向操作时减慢点击速度
            if not was_direction_active and hasattr(self.simulator, 'slow_click_interval'):
                self.simulator.slow_click_interval(True)
            
            # 记录日志
            logging.info("YOLO模型检测到向右拉状态，按下D键")
            
            # 按下D键 (注意：这里应该是D键，而不是A键，因为向右拉应该按D)
            self.key_controller.handle_direction("right")
        
        # 检测到向左拉状态
        elif FishingState.PULL_LEFT.value in detected_states:
            # 标记方向操作激活
            was_direction_active = self.direction_active
            self.direction_active = True
            
            # 首次激活方向操作时减慢点击速度
            if not was_direction_active and hasattr(self.simulator, 'slow_click_interval'):
                self.simulator.slow_click_interval(True)
            
            # 记录日志
            logging.info("YOLO模型检测到向左拉状态，按下A键")
            
            # 按下A键 (注意：这里应该是A键，而不是D键，因为向左拉应该按A)
            self.key_controller.handle_direction("left")
        
        # 没有检测到方向操作状态
        elif self.direction_active:
            # 恢复点击速度
            if hasattr(self.simulator, 'slow_click_interval'):
                self.simulator.slow_click_interval(False)
            
            # 重置方向操作标志
            self.direction_active = False
            
            # 记录日志
            logging.debug("方向操作结束，恢复点击速度")
    
    def _start_rapid_clicking(self):
        """
        开始快速点击
        
        启动一个独立线程，专注于执行快速点击操作。
        实现按下0.054s-0.127s后弹起，弹起0.054s-0.127s后按下的循环模式。
        """
        logging.info("准备开始快速点击...")
        
        # 如果已有点击线程在运行，则不需要重新启动
        if hasattr(self, 'clicking_thread') and self.clicking_thread is not None:
            if self.clicking_thread.is_alive():
                if not self.stop_clicking:
                    logging.info("快速点击已在进行中，无需重新启动")
                    return
                else:
                    # 如果线程存在但停止标志为True，先停止它
                    logging.info("存在停止状态的点击线程，先停止它")
                    self._stop_rapid_clicking()
        
        # 重置停止标志
        self.stop_clicking = False
        
        # 确保鼠标弹起状态
        try:
            pyautogui.mouseUp(button='left')
        except Exception:
            pass
        
        # 创建并启动点击线程
        try:
            self.clicking_thread = threading.Thread(
                target=self._rapid_clicking_worker,
                daemon=True,
                name="RapidClickingThread"
            )
            self.clicking_thread.start()
            
            # 等待线程确实启动
            time.sleep(0.05)
            
            # 检查线程是否成功启动
            if self.clicking_thread.is_alive():
                logging.info("快速点击线程已成功启动")
            else:
                logging.error("快速点击线程启动失败")
        except Exception as e:
            logging.error(f"创建快速点击线程失败: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
    
    def _stop_rapid_clicking(self):
        """
        停止快速点击
        """
        logging.info("尝试停止快速点击...")
        
        # 设置停止标志
        self.stop_clicking = True
        
        # 确保鼠标弹起
        try:
            pyautogui.mouseUp(button='left')
            logging.info("已确保鼠标左键弹起")
        except Exception as e:
            logging.error(f"确保鼠标弹起时出错: {str(e)}")
        
        # 等待线程结束
        if hasattr(self, 'clicking_thread') and self.clicking_thread is not None:
            if self.clicking_thread.is_alive():
                try:
                    # 检查是否是当前线程
                    if self.clicking_thread != threading.current_thread():
                        self.clicking_thread.join(timeout=0.5)
                        if self.clicking_thread.is_alive():
                            logging.warning("快速点击线程未能及时停止，将被强制终止")
                        else:
                            logging.info("快速点击线程已成功停止")
                except Exception as e:
                    logging.error(f"等待点击线程结束时出错: {str(e)}")
        
        # 重置点击线程引用
        self.clicking_thread = None
    
    def _rapid_clicking_worker(self):
        """
        快速点击工作线程
        
        这是一个完全独立的线程，持续进行点击操作，不受状态识别的影响。
        实现按下0.054s-0.127s后弹起，弹起0.054s-0.127s后按下的循环模式。
        """
        logging.info("快速点击线程已启动")
        
        # 确保停止标志为False
        self.stop_clicking = False
        
        # 记录开始时间
        start_time = time.time()
        click_count = 0
        last_log_time = start_time
        
        # 确保鼠标弹起状态
        try:
            pyautogui.mouseUp(button='left')
        except Exception:
            pass
        
        try:
            # 开始循环点击
            while not self.stop_clicking and self.is_running and not self.is_paused:
                try:
                    # 检查是否需要停止
                    if self.stop_clicking or not self.is_running or self.is_paused:
                        logging.info("检测到停止标志，退出点击循环")
                        break
                    
                    # 执行鼠标按下操作
                    pyautogui.mouseDown(button='left')
                    
                    # 等待随机时间后弹起
                    down_time = random.uniform(
                        self.simulator.click_interval_min, 
                        self.simulator.click_interval_max
                    )
                    
                    # 使用精确的计时方法，但频繁检查停止标志
                    end_down = time.perf_counter() + down_time
                    while time.perf_counter() < end_down:
                        if self.stop_clicking or not self.is_running or self.is_paused:
                            break
                        time.sleep(0.001)  # 短暂睡眠，减少CPU使用
                    
                    # 再次检查停止标志
                    if self.stop_clicking or not self.is_running or self.is_paused:
                        break
                    
                    # 执行鼠标弹起操作
                    pyautogui.mouseUp(button='left')
                    
                    # 增加点击计数
                    click_count += 1
                    
                    # 每秒记录一次日志
                    current_time = time.time()
                    if current_time - last_log_time >= 1.0:
                        elapsed = current_time - start_time
                        rate = click_count / elapsed if elapsed > 0 else 0
                        logging.info(f"循环点击中: {click_count}次循环, {rate:.2f}次/秒")
                        last_log_time = current_time
                    
                    # 再次检查停止标志
                    if self.stop_clicking or not self.is_running or self.is_paused:
                        break
                    
                    # 等待随机时间后再次按下
                    up_time = random.uniform(
                        self.simulator.click_interval_min, 
                        self.simulator.click_interval_max
                    )
                    
                    # 使用精确的计时方法，但频繁检查停止标志
                    end_up = time.perf_counter() + up_time
                    while time.perf_counter() < end_up:
                        if self.stop_clicking or not self.is_running or self.is_paused:
                            break
                        time.sleep(0.001)  # 短暂睡眠，减少CPU使用
                    
                except Exception as e:
                    logging.error(f"单次点击操作出错: {str(e)}")
                    # 确保鼠标弹起
                    try:
                        pyautogui.mouseUp(button='left')
                    except Exception:
                        pass
                    # 短暂暂停后继续
                    time.sleep(0.01)
        
        except Exception as e:
            logging.error(f"循环点击线程出错: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
        
        finally:
            # 确保鼠标弹起
            try:
                pyautogui.mouseUp(button='left')
                logging.info("确保鼠标左键弹起")
            except Exception as e:
                logging.error(f"确保鼠标弹起时出错: {str(e)}")
            
            # 记录点击统计
            elapsed = time.time() - start_time
            rate = click_count / elapsed if elapsed > 0 else 0
            logging.info(f"循环点击结束: 总计{click_count}次循环, 平均{rate:.2f}次/秒, 持续{elapsed:.2f}秒")

    def set_debug_mode(self, debug_mode: bool):
        """
        设置调试模式
        
        Args:
            debug_mode: 是否开启调试模式
        """
        self.debug_mode = debug_mode
        logging.info(f"调试模式已{'开启' if debug_mode else '关闭'}")
    
    def set_state_detection_threshold(self, threshold: int):
        """
        设置状态检测阈值
        
        Args:
            threshold: 状态检测阈值（连续检测到几次才确认状态变化）
        """
        self.state_detection_threshold = max(1, threshold)
        logging.info(f"状态检测阈值已设置为: {self.state_detection_threshold}")
    
    def get_state_detection_counts(self) -> Dict[FishingState, int]:
        """
        获取状态检测计数
        
        Returns:
            状态检测计数字典
        """
        return self.state_detection_counters.copy()
    
    def get_current_state(self) -> FishingState:
        """
        获取当前状态
        
        Returns:
            当前状态
        """
        return self.current_state
    
    def get_previous_state(self) -> Optional[FishingState]:
        """
        获取上一个状态
        
        Returns:
            上一个状态
        """
        return self.previous_state
    
    def get_state_durations(self) -> Dict[FishingState, float]:
        """
        获取状态持续时间
        
        Returns:
            状态持续时间字典
        """
        # 更新当前状态的持续时间
        current_time = time.time()
        duration = current_time - self.state_change_time
        self.state_durations[self.current_state] += duration
        self.state_change_time = current_time
        
        return self.state_durations.copy()
    
    def log_state_info(self):
        """
        记录状态信息
        """
        # 获取状态持续时间
        state_durations = self.get_state_durations()
        total_time = sum(state_durations.values())
        
        if total_time > 0:
            # 计算状态占比
            state_percentages = {
                state.name: (duration / total_time) * 100
                for state, duration in state_durations.items()
                if duration > 0
            }
            
            # 按占比排序
            sorted_states = sorted(
                state_percentages.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # 记录日志
            logging.info("状态占比统计:")
            for state_name, percentage in sorted_states:
                logging.info(f"  {state_name}: {percentage:.1f}%")
        
        # 记录状态检测计数
        logging.info("状态检测计数:")
        for state, count in self.state_detection_counters.items():
            if count > 0:
                logging.info(f"  {state.name}: {count}")
    
    def test_state_detection(self, duration: float = 5.0):
        """
        测试状态检测
        
        Args:
            duration: 测试持续时间（秒）
        """
        logging.info(f"开始测试状态检测，持续{duration}秒...")
        
        # 记录开始时间
        start_time = time.time()
        
        # 重置状态检测计数器
        for state in FishingState:
            self.state_detection_counters[state] = 0
        
        # 测试状态检测
        while time.time() - start_time < duration:
            # 获取当前检测到的状态
            detected_states = self.detector.get_current_state()
            
            # 更新状态检测计数器
            for state_id, confidence in detected_states.items():
                if state_id in [s.value for s in FishingState]:
                    self.state_detection_counters[FishingState(state_id)] += 1
            
            # 记录检测到的状态
            if detected_states and self.debug_mode:
                states_str = ", ".join([
                    f"{self.detector.get_state_name(state_id)}({conf:.2f})"
                    for state_id, conf in detected_states.items()
                ])
                logging.debug(f"检测到的状态: {states_str}")
            
            # 短暂休眠
            time.sleep(0.1)
        
        # 记录测试结果
        logging.info("状态检测测试结果:")
        for state, count in self.state_detection_counters.items():
            if count > 0:
                rate = count / duration
                logging.info(f"  {state.name}: {count}次 ({rate:.1f}次/秒)")
        
        # 重置状态检测计数器
        for state in FishingState:
            self.state_detection_counters[state] = 0


# 单例模式
_instance = None

def get_instance():
    """
    获取钓鱼状态机单例
    
    Returns:
        FishingStateMachine实例
    """
    global _instance
    if _instance is None:
        _instance = FishingStateMachine()
    return _instance 