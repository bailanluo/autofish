"""
Fisher钓鱼模块核心控制器
实现钓鱼状态机逻辑和多线程协调，协调模型检测、OCR识别和输入控制

作者: AutoFish Team
版本: v1.0
创建时间: 2024-12-28
"""

import time
import threading
from enum import Enum
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass

from .config import fisher_config
from .model_detector import model_detector
from .ocr_detector import ocr_detector
from .input_controller import input_controller


class FishingState(Enum):
    """钓鱼状态枚举"""
    STOPPED = "停止状态"
    WAITING_INITIAL = "等待初始状态"
    WAITING_HOOK = "等待上钩状态" 
    FISH_HOOKED = "鱼上钩状态"
    PULLING_NORMAL = "提线中_耐力未到二分之一"
    PULLING_HALFWAY = "提线中_耐力已到二分之一"
    SUCCESS = "钓鱼成功状态"
    CASTING = "抛竿状态"
    ERROR = "错误状态"


@dataclass
class FishingStatus:
    """钓鱼状态信息"""
    current_state: FishingState = FishingState.STOPPED
    current_detected_state: Optional[int] = None  # 当前检测到的YOLO状态
    current_ocr_state: Optional[int] = None  # 当前检测到的OCR状态  
    confidence: float = 0.0  # 检测置信度
    round_count: int = 0  # 钓鱼轮数
    start_time: Optional[float] = None  # 开始时间
    error_message: str = ""  # 错误信息
    

class FishingController:
    """钓鱼控制器"""
    
    def __init__(self):
        """
        初始化钓鱼控制器
        """
        # 控制器状态
        self.status = FishingStatus()
        self.is_running = False  # 运行状态
        self.should_stop = False  # 停止标志
        
        # 线程管理
        self.main_thread: Optional[threading.Thread] = None  # 主控制线程
        self.ocr_thread: Optional[threading.Thread] = None  # OCR线程
        self.thread_lock = threading.Lock()  # 线程锁
        
        # 事件通信
        self.ocr_active = threading.Event()  # OCR激活事件
        self.ocr_stop = threading.Event()  # OCR停止事件
        
        # 回调函数
        self.status_callback: Optional[Callable] = None  # 状态更新回调
        
        # 超时管理
        self.timeout_start: Optional[float] = None  # 超时开始时间
        
        print("钓鱼控制器初始化完成")
    
    def set_status_callback(self, callback: Callable[[FishingStatus], None]) -> None:
        """
        设置状态更新回调函数
        
        Args:
            callback: 状态更新回调函数
        """
        self.status_callback = callback
    
    def _update_status(self, state: Optional[FishingState] = None, 
                      detected_state: Optional[int] = None,
                      confidence: Optional[float] = None,
                      error_message: Optional[str] = None) -> None:
        """
        更新钓鱼状态
        
        Args:
            state: 新的钓鱼状态
            detected_state: 检测到的状态编号
            confidence: 检测置信度
            error_message: 错误信息
        """
        with self.thread_lock:
            if state is not None:
                self.status.current_state = state
            if detected_state is not None:
                self.status.current_detected_state = detected_state
            if confidence is not None:
                self.status.confidence = confidence
            if error_message is not None:
                self.status.error_message = error_message
        
        # 调用回调函数
        if self.status_callback:
            try:
                self.status_callback(self.status)
            except Exception as e:
                print(f"状态回调失败: {e}")
    
    def _ocr_worker(self) -> None:
        """
        OCR工作线程
        在状态2和3时持续检测方向文字并执行对应按键
        """
        print("OCR线程启动")
        
        while not self.ocr_stop.is_set():
            # 等待OCR激活信号
            if self.ocr_active.wait(timeout=0.1):
                try:
                    # 检测方向文字
                    direction_result = ocr_detector.detect_direction_text_with_confidence()
                    
                    if direction_result:
                        direction_state = direction_result['state']
                        self.status.current_ocr_state = direction_state
                        
                        # 根据方向执行按键
                        input_controller.handle_direction_key(direction_state)
                        
                        print(f"OCR检测到方向: {direction_result['text']} (状态{direction_state})")
                    
                    # OCR检测间隔
                    time.sleep(fisher_config.ocr.detection_interval)
                    
                except Exception as e:
                    print(f"OCR检测失败: {e}")
                    time.sleep(0.5)
            
            # 检查是否需要停止OCR
            if not self.ocr_active.is_set():
                self.status.current_ocr_state = None
        
        print("OCR线程结束")
    
    def _start_ocr_thread(self) -> None:
        """启动OCR线程"""
        if not self.ocr_thread or not self.ocr_thread.is_alive():
            self.ocr_stop.clear()
            self.ocr_thread = threading.Thread(target=self._ocr_worker, daemon=True)
            self.ocr_thread.start()
    
    def _activate_ocr(self) -> None:
        """激活OCR检测"""
        self._start_ocr_thread()
        self.ocr_active.set()
        print("OCR检测已激活")
    
    def _deactivate_ocr(self) -> None:
        """停用OCR检测"""
        self.ocr_active.clear()
        print("OCR检测已停用")
    
    def _wait_for_initial_state(self) -> bool:
        """
        等待初始状态 (状态0或1)
        
        Returns:
            bool: 是否成功检测到初始状态
        """
        print("等待检测到初始状态 (0或1)...")
        self._update_status(FishingState.WAITING_INITIAL)
        self.timeout_start = time.time()
        
        timeout = fisher_config.timing.initial_timeout
        
        while not self.should_stop:
            # 检查超时
            if time.time() - self.timeout_start > timeout:
                error_msg = f"初始状态检测超时 ({timeout}秒)"
                print(error_msg)
                self._update_status(FishingState.ERROR, error_message=error_msg)
                return False
            
            # 检测状态0或1
            result = model_detector.detect_multiple_states([0, 1])
            if result:
                detected_state = result['state']
                confidence = result['confidence']
                
                print(f"检测到初始状态: {detected_state} (置信度: {confidence:.2f})")
                self._update_status(detected_state=detected_state, confidence=confidence)
                
                if detected_state == 0:
                    self._update_status(FishingState.WAITING_HOOK)
                    return True
                elif detected_state == 1:
                    self._update_status(FishingState.FISH_HOOKED)
                    return self._handle_fish_hooked()
            
            time.sleep(fisher_config.model.detection_interval)
        
        return False
    
    def _wait_for_hook(self) -> bool:
        """
        等待鱼上钩 (状态1)
        
        Returns:
            bool: 是否成功检测到鱼上钩
        """
        print("等待鱼上钩...")
        
        while not self.should_stop:
            # 检查超时
            if time.time() - self.timeout_start > fisher_config.timing.initial_timeout:
                error_msg = f"等待上钩超时 ({fisher_config.timing.initial_timeout}秒)"
                print(error_msg)
                self._update_status(FishingState.ERROR, error_message=error_msg)
                return False
            
            # 检测状态1
            result = model_detector.detect_specific_state(1)
            if result:
                print("检测到鱼上钩！")
                self._update_status(FishingState.FISH_HOOKED, detected_state=1)
                return self._handle_fish_hooked()
            
            time.sleep(fisher_config.model.detection_interval)
        
        return False
    
    def _handle_fish_hooked(self) -> bool:
        """
        处理鱼上钩状态
        
        Returns:
            bool: 是否成功处理
        """
        print("开始快速点击...")
        
        # 启动快速点击
        if not input_controller.start_clicking():
            print("启动快速点击失败")
            return False
        
        # 进入提线阶段
        return self._handle_pulling_phase()
    
    def _handle_pulling_phase(self) -> bool:
        """
        处理提线阶段 (状态2和3的切换)
        
        Returns:
            bool: 是否成功完成提线阶段
        """
        print("进入提线阶段...")
        
        # 启动OCR检测
        self._activate_ocr()
        
        while not self.should_stop:
            # 检测当前状态
            result = model_detector.detect_multiple_states([2, 3, 6])
            
            if not result:
                time.sleep(fisher_config.model.detection_interval)
                continue
            
            detected_state = result['state']
            confidence = result['confidence']
            
            self._update_status(detected_state=detected_state, confidence=confidence)
            
            if detected_state == 2:  # 提线中_耐力未到二分之一
                if self.status.current_state != FishingState.PULLING_NORMAL:
                    print("状态2: 继续快速点击")
                    self._update_status(FishingState.PULLING_NORMAL)
                    input_controller.resume_clicking()
                
            elif detected_state == 3:  # 提线中_耐力已到二分之一
                if self.status.current_state != FishingState.PULLING_HALFWAY:
                    print("状态3: 暂停点击")
                    self._update_status(FishingState.PULLING_HALFWAY)
                    input_controller.pause_clicking()
                    
                    # 等待1秒后重新检测
                    time.sleep(fisher_config.timing.state3_pause_time)
                
            elif detected_state == 6:  # 钓鱼成功
                print("检测到钓鱼成功状态！")
                
                # 停止点击和OCR
                input_controller.stop_clicking()
                self._deactivate_ocr()
                
                return self._handle_success()
            
            time.sleep(fisher_config.model.detection_interval)
        
        return False
    
    def _handle_success(self) -> bool:
        """
        处理钓鱼成功状态
        
        Returns:
            bool: 是否成功处理
        """
        print("处理钓鱼成功状态...")
        self._update_status(FishingState.SUCCESS, detected_state=6)
        
        while not self.should_stop:
            # 等待1.5秒后按f键
            if input_controller.wait_and_handle_success():
                # 检查状态6是否消失
                result = model_detector.detect_specific_state(6)
                if not result:
                    print("成功状态已消失，准备抛竿")
                    return self._handle_casting()
                else:
                    print("成功状态仍存在，继续按f键")
            else:
                print("处理成功状态失败")
                return False
        
        return False
    
    def _handle_casting(self) -> bool:
        """
        处理抛竿状态
        
        Returns:
            bool: 是否成功抛竿
        """
        print("执行抛竿操作...")
        self._update_status(FishingState.CASTING)
        
        # 执行抛竿
        if input_controller.cast_rod():
            # 增加轮数计数
            self.status.round_count += 1
            print(f"抛竿完成，开始第 {self.status.round_count + 1} 轮钓鱼")
            
            # 等待抛竿动画完成
            time.sleep(1.0)
            
            return True
        else:
            print("抛竿失败")
            return False
    
    def _main_loop(self) -> None:
        """主控制循环"""
        print("钓鱼主循环启动")
        
        try:
            while not self.should_stop:
                # 等待初始状态
                if not self._wait_for_initial_state():
                    break
                
                # 如果是状态0，等待状态1
                if self.status.current_detected_state == 0:
                    if not self._wait_for_hook():
                        break
                
                # 抛竿并准备下一轮
                if not self._handle_casting():
                    break
                
                print(f"第 {self.status.round_count} 轮钓鱼完成")
        
        except Exception as e:
            error_msg = f"主循环异常: {e}"
            print(error_msg)
            self._update_status(FishingState.ERROR, error_message=error_msg)
        
        finally:
            self._cleanup()
            print("钓鱼主循环结束")
    
    def start_fishing(self) -> bool:
        """
        开始钓鱼
        
        Returns:
            bool: 是否成功启动
        """
        if self.is_running:
            print("钓鱼已在运行中")
            return False
        
        # 检查初始化状态
        if not model_detector.is_initialized:
            print("模型检测器未初始化")
            return False
        
        if not ocr_detector.is_initialized:
            print("OCR检测器未初始化")
            return False
        
        # 重置状态
        self.status = FishingStatus()
        self.status.start_time = time.time()
        self.should_stop = False
        self.is_running = True
        
        # 启动主线程
        self.main_thread = threading.Thread(target=self._main_loop, daemon=True)
        self.main_thread.start()
        
        print("钓鱼已启动")
        return True
    
    def stop_fishing(self) -> bool:
        """
        停止钓鱼
        
        Returns:
            bool: 是否成功停止
        """
        if not self.is_running:
            print("钓鱼未在运行")
            return False
        
        print("正在停止钓鱼...")
        self.should_stop = True
        
        # 等待主线程结束
        if self.main_thread and self.main_thread.is_alive():
            self.main_thread.join(timeout=3.0)
        
        self._cleanup()
        self.is_running = False
        self._update_status(FishingState.STOPPED)
        
        print("钓鱼已停止")
        return True
    
    def _cleanup(self) -> None:
        """清理资源"""
        print("清理钓鱼控制器资源...")
        
        # 停用OCR
        self._deactivate_ocr()
        self.ocr_stop.set()
        
        # 停止输入操作
        input_controller.emergency_stop()
        
        # 等待OCR线程结束
        if self.ocr_thread and self.ocr_thread.is_alive():
            self.ocr_thread.join(timeout=2.0)
    
    def get_status(self) -> FishingStatus:
        """
        获取当前钓鱼状态
        
        Returns:
            FishingStatus: 当前状态
        """
        return self.status
    
    def emergency_stop(self) -> None:
        """紧急停止"""
        print("执行紧急停止")
        self.should_stop = True
        self._cleanup()
        self.is_running = False
        self._update_status(FishingState.STOPPED, error_message="紧急停止")

# 全局钓鱼控制器实例
fishing_controller = FishingController() 