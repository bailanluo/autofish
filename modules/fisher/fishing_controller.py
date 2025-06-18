"""
Fisher钓鱼模块核心控制器
实现钓鱼状态机逻辑和多线程协调，协调模型检测和输入控制

作者: AutoFish Team
版本: v1.0.13
创建时间: 2024-12-28
更新时间: 2025-01-17

修复历史:
v1.0.13: 集成统一日志系统，替换print语句，解决内存占用问题
v1.0.12: 适配新模型状态映射，移除状态4/5，将原状态6改为状态4(钓鱼成功)
v1.0.11: 修复状态4/5识别问题，添加对向左拉/向右拉状态的处理，解决卡在鱼上钩状态的问题
v1.0.10: 动态检测间隔系统优化
v1.0.9: 状态机逻辑修正，完全移除OCR依赖
"""

import time
import threading
from enum import Enum
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass

# 导入统一日志系统
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from logger import setup_logger

from .config import fisher_config
from .model_detector import model_detector
from .input_controller import input_controller

# 设置日志记录器
logger = setup_logger('fisher')

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
        self.thread_lock = threading.Lock()  # 线程锁
        
        # 简单按键循环相关
        self.key_cycle_thread: Optional[threading.Thread] = None  # 按键循环线程
        self.key_cycle_stop = threading.Event()  # 按键循环停止事件
        
        # 回调函数
        self.status_callback: Optional[Callable] = None  # 状态更新回调
        
        # 超时管理
        self.timeout_start: Optional[float] = None  # 超时开始时间
        
        logger.info("钓鱼控制器初始化完成")
    
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
                logger.error(f"状态回调失败: {e}")
    
    def _key_cycle_worker(self) -> None:
        """
        简单按键循环工作线程
        循环执行：按a键1.5秒 → 等待0.5秒 → 按d键1.5秒 → 等待0.5秒
        """
        logger.info("按键循环线程启动")
        
        key_sequence = ['a', 'd']  # 按键序列：a键和d键
        key_index = 0  # 当前按键索引
        
        while not self.key_cycle_stop.is_set():
            try:
                # 获取当前要按的键
                current_key = key_sequence[key_index]
                
                logger.info(f"按键循环: 长按 {current_key} 键1.5秒")
                
                # 长按当前键1.5秒
                if input_controller.press_key(current_key, 1.5):
                    logger.info(f"按键 {current_key} 执行完成")
                else:
                    logger.info(f"按键 {current_key} 执行失败")
                
                # 等待0.5秒
                if not self.key_cycle_stop.wait(timeout=0.5):
                    # 切换到下一个键
                    key_index = (key_index + 1) % len(key_sequence)
                else:
                    break
                    
            except Exception as e:
                logger.error(f"按键循环异常: {e}")
                time.sleep(0.5)
        
        logger.info("按键循环线程结束")
    
    def _start_key_cycle(self) -> None:
        """启动按键循环"""
        if not self.key_cycle_thread or not self.key_cycle_thread.is_alive():
            self.key_cycle_stop.clear()
            self.key_cycle_thread = threading.Thread(target=self._key_cycle_worker, daemon=True)
            self.key_cycle_thread.start()
            logger.info("按键循环已启动")
    
    def _stop_key_cycle(self) -> None:
        """停止按键循环"""
        self.key_cycle_stop.set()
        logger.info("按键循环已停止")
    
    def _wait_for_initial_state(self) -> bool:
        """
        等待初始状态 (状态0或1)
        优化检测逻辑：如果检测到状态1，不立即确认，而是进入累计确认流程
        
        Returns:
            bool: 是否成功检测到初始状态
        """
        logger.info("🔍 等待检测到初始状态 (0或1)...")
        timeout = fisher_config.timing.initial_timeout
        detection_count = 0
        
        while not self.should_stop:
            # 检查超时
            elapsed = time.time() - self.timeout_start
            if elapsed > timeout:
                error_msg = f"初始状态检测超时 ({timeout}秒)"
                logger.error(f"⏰ {error_msg}")
                self._update_status(FishingState.ERROR, error_message=error_msg)
                return False
            
            detection_count += 1
            if detection_count % 50 == 0:  # 每5秒输出一次进度
                logger.info(f"🔍 初始状态检测中... 已尝试 {detection_count} 次，耗时 {elapsed:.1f}秒")
            
            # 检测状态0或1
            result = model_detector.detect_multiple_states([0, 1])
            if result:
                detected_state = result['state']
                confidence = result['confidence']
                
                logger.info(f"✅ 检测到初始状态: {detected_state} (置信度: {confidence:.2f})")
                self._update_status(detected_state=detected_state, confidence=confidence)
                
                if detected_state == 0:
                    logger.info("📌 设置状态为：等待上钩")
                    self._update_status(FishingState.WAITING_HOOK)
                    return True
                elif detected_state == 1:
                    logger.info("📌 检测到状态1，需要进行累计确认...")
                    # 不立即确认状态1，让主循环调用_wait_for_hook()进行累计确认
                    self._update_status(FishingState.WAITING_HOOK)  # 先设置为等待状态
                    return True
            
            time.sleep(fisher_config.model.detection_interval)
        
        logger.info("🛑 初始状态检测被中断")
        return False
    
    def _wait_for_hook(self) -> bool:
        """
        等待鱼上钩 (状态1)
        优化流程控制：需要累计识别到3次状态1才算有效，避免误判
        
        Returns:
            bool: 是否成功检测到鱼上钩
        """
        logger.info("🎣 等待鱼上钩...")
        detection_count = 0
        state1_confirm_count = 0  # 状态1累计确认次数（局部变量，每轮钓鱼重新计数）
        required_confirms = 3     # 需要累计确认的次数
        
        while not self.should_stop:
            # 检查超时
            elapsed = time.time() - self.timeout_start
            if elapsed > fisher_config.timing.initial_timeout:
                error_msg = f"等待上钩超时 ({fisher_config.timing.initial_timeout}秒)"
                logger.error(f"⏰ {error_msg}")
                self._update_status(FishingState.ERROR, error_message=error_msg)
                return False
            
            detection_count += 1
            if detection_count % 50 == 0:  # 每5秒输出一次进度
                logger.info(f"🎣 等待鱼上钩中... 已尝试 {detection_count} 次，耗时 {elapsed:.1f}秒")
                if state1_confirm_count > 0:
                    logger.info(f"    📊 状态1累计确认: {state1_confirm_count}/{required_confirms} 次")
            
            # 检测状态1
            result = model_detector.detect_multiple_states([1])
            if result:
                confidence = result['confidence']
                state1_confirm_count += 1
                logger.info(f"🐟 检测到状态1 第{state1_confirm_count}次确认 (置信度: {confidence:.2f}) [{state1_confirm_count}/{required_confirms}]")
                
                # 只有累计确认3次才算真正的鱼上钩
                if state1_confirm_count >= required_confirms:
                    logger.info(f"✅ 状态1已累计确认 {required_confirms} 次，确认鱼已上钩！")
                    self._update_status(FishingState.FISH_HOOKED, detected_state=1, confidence=confidence)
                    return True  # 修复：返回True让主循环处理，而不是直接调用处理流程
                else:
                    logger.info(f"⏳ 状态1需要再确认 {required_confirms - state1_confirm_count} 次")
            
            time.sleep(fisher_config.model.detection_interval)
        
        logger.info("🛑 等待鱼上钩被中断")
        return False
    
    def _handle_fish_hooked(self) -> bool:
        """
        处理鱼上钩状态
        
        Returns:
            bool: 是否成功处理
        """
        logger.info("🐟 开始处理鱼上钩状态...")
        logger.info("🖱️  启动快速点击...")
        
        # 启动快速点击
        if not input_controller.start_clicking():
            logger.error("❌ 启动快速点击失败")
            return False
        
        logger.info("✅ 快速点击已启动")
        logger.info("🎯 进入提线阶段...")
        
        # 进入提线阶段
        result = self._handle_pulling_phase()
        
        if result:
            logger.info("✅ 提线阶段处理成功")
        else:
            logger.error("❌ 提线阶段处理失败")
        
        return result
    
    def _handle_pulling_phase(self) -> bool:
        """
        处理提线阶段 (状态2和3的切换)
        使用简单的按键循环替代OCR识别
        
        Returns:
            bool: 是否成功完成提线阶段
        """
        logger.info("🎯 进入提线阶段...")
        
        # 启动简单按键循环（替代OCR）
        logger.info("⌨️  启动按键循环（a/d键切换）...")
        self._start_key_cycle()
        
        # 初始化状态检测
        previous_detected_state = None
        no_detection_count = 0  # 连续无检测次数
        total_detection_count = 0  # 总检测次数
        pulling_start = time.time()  # 用于统计时间，不用于超时
        
        logger.info(f"🔍 开始检测提线状态（状态2/3/4/5/6），无超时限制")
        
        while not self.should_stop:
            
            total_detection_count += 1
            
            # 检测当前状态 - 更新状态检测范围（移除状态4和5，状态6改为状态4）
            result = model_detector.detect_multiple_states([2, 3, 4])
            
            # 添加详细的调试检测 - 每100次输出一次详细信息（减少频率）
            if total_detection_count % 100 == 0:
                # 获取原始检测结果（不过滤目标状态）
                try:
                    # 先检查截图是否正常
                    debug_image = model_detector.capture_screen()
                    if debug_image is None:
                        logger.error(f"🔍 [调试] ❌ 屏幕截图失败")
                    else:
                        logger.info(f"🔍 [调试] 📸 截图成功，尺寸: {debug_image.shape}")
                        
                        # 执行模型推理，使用更低的置信度阈值
                        if model_detector.model is not None:
                            raw_results = model_detector.model(debug_image, conf=0.1, verbose=False)
                            
                            if len(raw_results) > 0 and len(raw_results[0].boxes) > 0:
                                boxes = raw_results[0].boxes
                                confidences = boxes.conf.cpu().numpy()
                                classes = boxes.cls.cpu().numpy().astype(int)
                                
                                logger.info(f"🔍 [调试] 🎯 检测到 {len(classes)} 个目标:")
                                for i, (cls, conf) in enumerate(zip(classes, confidences)):
                                    state_name = model_detector.state_names.get(cls, f"未知状态_{cls}")
                                    target_marker = "🎉" if cls in [2, 3, 4] else "⚪"
                                    thresh_marker = "✅" if conf >= fisher_config.model.confidence_threshold else "❌"
                                    logger.info(f"      {target_marker} [{i+1}] 状态{cls}({state_name}) - 置信度:{conf:.3f} {thresh_marker}")
                            else:
                                logger.error(f"🔍 [调试] ❌ 模型推理无结果 (置信度阈值0.1)")
                        else:
                            logger.error(f"🔍 [调试] ❌ 模型对象为空")
                            
                        # 使用标准检测方法再次验证
                        debug_result = model_detector.detect_states()
                        if debug_result:
                            logger.info(f"🔍 [调试] 🏆 最佳检测: 状态{debug_result['state']}({debug_result['state_name']}) - 置信度:{debug_result['confidence']:.3f}")
                        else:
                            logger.error(f"🔍 [调试] ❌ 标准检测方法也无结果")
                            
                except Exception as e:
                    logger.error(f"🔍 [调试] 💥 调试检测异常: {e}")
                    import traceback
                    traceback.print_exc()
            
            if not result:
                no_detection_count += 1
                if no_detection_count % 500 == 0:  # 每50秒输出一次调试信息（减少频率）
                    elapsed = time.time() - pulling_start
                    logger.info(f"�� 提线阶段无法检测到状态2/3/4，已尝试 {no_detection_count} 次，耗时 {elapsed:.1f}秒")
                    logger.info(f"📊 检测统计：总检测 {total_detection_count} 次，成功率 {((total_detection_count-no_detection_count)/total_detection_count*100):.1f}%")
                    
                    # 输出当前实际检测到的状态 - 详细诊断
                    logger.info(f"🔧 [详细诊断] 开始全面检测分析...")
                    
                    # 检测器状态检查
                    logger.info(f"🔧 模型检测器状态: {'✅初始化完成' if model_detector.is_initialized else '❌未初始化'}")
                    logger.info(f"🔧 模型对象状态: {'✅正常' if model_detector.model is not None else '❌空对象'}")
                    
                    # 屏幕截图检查
                    diag_image = model_detector.capture_screen()
                    if diag_image is None:
                        logger.error(f"🔧 截图状态: ❌失败 - 可能是屏幕截图工具问题")
                    else:
                        logger.info(f"🔧 截图状态: ✅成功 - 尺寸:{diag_image.shape}")
                        
                        # 使用极低阈值检测所有可能的状态
                        try:
                            ultra_low_results = model_detector.model(diag_image, conf=0.01, verbose=False)
                            if len(ultra_low_results) > 0 and len(ultra_low_results[0].boxes) > 0:
                                boxes = ultra_low_results[0].boxes
                                confidences = boxes.conf.cpu().numpy()
                                classes = boxes.cls.cpu().numpy().astype(int)
                                logger.info(f"🔧 超低阈值检测(0.01): 发现 {len(classes)} 个目标")
                                for cls, conf in zip(classes, confidences):
                                    state_name = model_detector.state_names.get(cls, f"未知状态_{cls}")
                                    logger.info(f"      状态{cls}({state_name}) - 置信度:{conf:.4f}")
                            else:
                                logger.error(f"🔧 超低阈值检测(0.01): ❌无任何检测结果")
                        except Exception as e:
                            logger.error(f"🔧 超低阈值检测异常: {e}")
                    
                    # 标准检测
                    current_detection = model_detector.detect_states()
                    if current_detection:
                        logger.info(f"📋 标准检测结果: 状态{current_detection['state']}({current_detection['state_name']}) - 置信度:{current_detection['confidence']:.3f}")
                    else:
                        logger.error(f"📋 标准检测结果: ❌无检测结果")
                    
                    logger.info(f"🔧 [详细诊断] 分析完毕")
                        
                # 临时修复：使用默认检测间隔或动态间隔
                pulling_interval = getattr(fisher_config.model, 'detection_interval_pulling', 0.04)
                time.sleep(pulling_interval)
                continue
            
            # 重置无检测计数（但不重置总计数）
            # no_detection_count = 0  # 保留累计，便于统计
            
            detected_state = result['state']
            confidence = result['confidence']
            
            logger.info(f"✅ 提线阶段检测到状态: {detected_state} (置信度: {confidence:.2f})")
            self._update_status(detected_state=detected_state, confidence=confidence)
            
            # 只有当状态发生变化时才进行处理，避免重复操作
            if detected_state != previous_detected_state:
                logger.info(f"🔄 状态变化: {previous_detected_state} → {detected_state}")
                
                if detected_state == 2:  # 提线中_耐力未到二分之一
                    logger.info("🟢 状态2: 继续快速点击")
                    self._update_status(FishingState.PULLING_NORMAL)
                    input_controller.resume_clicking()
                    
                elif detected_state == 3:  # 提线中_耐力已到二分之一
                    logger.info("🟡 状态3: 暂停点击")
                    self._update_status(FishingState.PULLING_HALFWAY)
                    input_controller.pause_clicking()
                    
                    # 等待1秒后重新检测
                    logger.info(f"⏸️  暂停 {fisher_config.timing.state3_pause_time}秒...")
                    time.sleep(fisher_config.timing.state3_pause_time)
                
                elif detected_state == 4:  # 钓鱼成功状态_txt
                    logger.info("🎉 检测到钓鱼成功状态！")
                    
                    # 停止点击和按键循环
                    logger.info("🛑 停止点击和按键循环...")
                    input_controller.stop_clicking()
                    self._stop_key_cycle()
                    
                    logger.info("🏆 提线阶段成功完成，进入成功处理...")
                    return self._handle_success()
                
                previous_detected_state = detected_state
            else:
                # 状态没有变化，输出简化日志
                if total_detection_count % 1000 == 0:  # 每100秒输出一次状态保持信息（减少频率）
                    elapsed = time.time() - pulling_start
                    logger.info(f"🔄 状态保持: {detected_state}，已持续 {elapsed:.1f}秒")
            
            # 临时修复：使用默认检测间隔或动态间隔
            pulling_interval = getattr(fisher_config.model, 'detection_interval_pulling', 0.04)
            time.sleep(pulling_interval)
        
        logger.info("🛑 提线阶段被中断")
        return False
    
    def _handle_success(self) -> bool:
        """
        处理钓鱼成功状态
        
        Returns:
            bool: 是否成功处理
        """
        logger.info("处理钓鱼成功状态...")
        self._update_status(FishingState.SUCCESS, detected_state=4)
        
        while not self.should_stop:
            # 等待1.5秒后按f键
            if input_controller.wait_and_handle_success():
                # 检查状态4是否消失
                result = model_detector.detect_specific_state(4)
                if not result:
                    logger.info("成功状态已消失，准备抛竿")
                    return self._handle_casting()
                else:
                    logger.info("成功状态仍存在，继续按f键")
            else:
                logger.error("处理成功状态失败")
                return False
        
        return False
    
    def _handle_casting(self) -> bool:
        """
        处理抛竿状态
        
        Returns:
            bool: 是否成功抛竿
        """
        logger.info("执行抛竿操作...")
        self._update_status(FishingState.CASTING)
        
        # 执行抛竿
        if input_controller.cast_rod():
            # 增加轮数计数
            self.status.round_count += 1
            logger.info(f"抛竿完成，开始第 {self.status.round_count} 轮钓鱼")
            
            # 等待抛竿动画完成
            time.sleep(1.0)
            
            return True
        else:
            logger.error("抛竿失败")
            return False
    
    def _main_loop(self) -> None:
        """主控制循环"""
        logger.info("🚀 钓鱼主循环启动")
        
        try:
            while not self.should_stop:
                logger.info(f"📍 主循环开始新一轮，当前状态: {self.status.current_state}")
                
                # 等待初始状态（状态0或1）
                logger.info("🔍 开始等待初始状态...")
                self._update_status(FishingState.WAITING_INITIAL)
                self.timeout_start = time.time()
                
                if not self._wait_for_initial_state():
                    logger.error("❌ 等待初始状态失败，退出主循环")
                    break
                
                logger.info(f"✅ 初始状态检测完成，检测到状态: {self.status.current_detected_state}")
                
                # 无论检测到状态0还是状态1，都需要进行累计确认
                logger.info("🎣 开始等待鱼上钩（需要累计确认）...")
                if not self._wait_for_hook():
                    logger.error("❌ 等待鱼上钩失败，退出主循环")
                    break
                
                logger.info(f"✅ 鱼上钩确认完成，当前检测状态: {self.status.current_detected_state}")
                
                # 处理鱼上钩状态
                if self.status.current_detected_state == 1:
                    logger.info("🐟 开始处理鱼上钩状态...")
                    if not self._handle_fish_hooked():
                        logger.error("❌ 处理鱼上钩状态失败，退出主循环")
                        break
                    logger.info("✅ 鱼上钩状态处理完成")
                else:
                    logger.warning(f"⚠️  警告：期望状态1，但当前检测状态为: {self.status.current_detected_state}")
                
                # 抛竿并准备下一轮
                logger.info("🎯 开始抛竿操作...")
                if not self._handle_casting():
                    logger.error("❌ 抛竿操作失败，退出主循环")
                    break
                
                logger.info(f"🎉 第 {self.status.round_count} 轮钓鱼完成")
        
        except Exception as e:
            error_msg = f"主循环异常: {e}"
            logger.error(f"💥 {error_msg}")
            import traceback
            traceback.print_exc()
            self._update_status(FishingState.ERROR, error_message=error_msg)
        
        finally:
            self._cleanup()
            logger.info("🏁 钓鱼主循环结束")
    
    def start_fishing(self) -> bool:
        """
        开始钓鱼
        
        Returns:
            bool: 是否成功启动
        """
        if self.is_running:
            logger.info("钓鱼已在运行中")
            return False
        
        # 检查初始化状态
        if not model_detector.is_initialized:
            logger.error("模型检测器未初始化")
            return False
        
        logger.info("正在准备钓鱼环境...")
        
        # 测试屏幕截图功能（新的MSS架构已无需重置）
        logger.info("验证屏幕截图功能...")
        
        # 测试屏幕截图功能
        logger.info("测试屏幕截图功能...")
        test_image = model_detector.capture_screen()
        if test_image is None:
            logger.error("❌ 屏幕截图测试失败，无法启动钓鱼")
            return False
        logger.info("✅ 屏幕截图测试通过")
        
        # 重置状态
        self.status = FishingStatus()
        self.status.start_time = time.time()
        self.should_stop = False
        self.is_running = True
        
        # 启动主线程
        self.main_thread = threading.Thread(target=self._main_loop, daemon=True)
        self.main_thread.start()
        
        logger.info("钓鱼已启动")
        return True
    
    def stop_fishing(self) -> bool:
        """
        停止钓鱼
        
        Returns:
            bool: 是否成功停止
        """
        if not self.is_running:
            logger.info("钓鱼未在运行")
            return False
        
        logger.info("正在停止钓鱼...")
        self.should_stop = True
        
        # 等待主线程结束
        if self.main_thread and self.main_thread.is_alive():
            self.main_thread.join(timeout=3.0)
        
        self._cleanup()
        self.is_running = False
        self._update_status(FishingState.STOPPED)
        
        logger.info("钓鱼已停止")
        return True
    
    def _cleanup(self) -> None:
        """清理资源"""
        logger.info("清理钓鱼控制器资源...")
        
        # 停止按键循环
        self._stop_key_cycle()
        
        # 停止输入操作
        input_controller.emergency_stop()
        
        # 等待按键循环线程结束
        if self.key_cycle_thread and self.key_cycle_thread.is_alive():
            self.key_cycle_thread.join(timeout=2.0)
        
        # 注意：新的MSS架构使用即用即释放模式，无需手动清理
    
    def get_status(self) -> FishingStatus:
        """
        获取当前钓鱼状态
        
        Returns:
            FishingStatus: 当前状态
        """
        return self.status
    
    def emergency_stop(self) -> None:
        """紧急停止"""
        logger.info("执行紧急停止")
        self.should_stop = True
        self._cleanup()
        self.is_running = False
        self._update_status(FishingState.STOPPED, error_message="紧急停止")

# 全局钓鱼控制器实例
fishing_controller = FishingController() 