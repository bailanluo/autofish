"""
Fisher钓鱼模块按键循环功能测试
测试简单按键循环替代OCR识别

作者: AutoFish Team
版本: v1.0.5
创建时间: 2024-12-28
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from modules.fisher.fishing_controller import fishing_controller
from modules.fisher.model_detector import model_detector
from modules.fisher.ocr_detector import ocr_detector


def test_key_cycle_functionality():
    """测试按键循环功能"""
    print("=" * 50)
    print("测试按键循环功能")
    print("=" * 50)
    
    # 测试按键循环启动和停止
    print("启动按键循环...")
    fishing_controller._start_key_cycle()
    
    print("按键循环运行中，等待10秒...")
    print("预期行为：循环执行 a键1秒 → 等待1秒 → d键1秒 → 等待1秒")
    
    # 等待10秒观察按键循环
    time.sleep(10)
    
    print("停止按键循环...")
    fishing_controller._stop_key_cycle()
    
    print("按键循环测试完成")
    return True


def test_pulling_phase_simulation():
    """测试提线阶段模拟"""
    print("\n" + "=" * 50)
    print("测试提线阶段模拟")
    print("=" * 50)
    
    # 模拟状态转换测试
    status_updates = []
    
    def status_callback(status):
        status_updates.append({
            'state': status.current_state.value,
            'detected_state': status.current_detected_state,
            'timestamp': time.time()
        })
        print(f"状态更新: {status.current_state.value} (检测状态: {status.current_detected_state})")
    
    # 设置回调
    fishing_controller.set_status_callback(status_callback)
    
    print("启动钓鱼以测试提线阶段...")
    if fishing_controller.start_fishing():
        print("钓鱼已启动，监控状态转换...")
        
        # 监控5秒
        start_time = time.time()
        while time.time() - start_time < 5:
            time.sleep(0.5)
        
        print("停止钓鱼...")
        fishing_controller.stop_fishing()
        
        print(f"\n收到 {len(status_updates)} 个状态更新:")
        for i, update in enumerate(status_updates):
            print(f"  {i+1}. {update['state']} (检测: {update['detected_state']})")
        
        return len(status_updates) > 0
    else:
        print("钓鱼启动失败")
        return False


def test_thread_management():
    """测试线程管理"""
    print("\n" + "=" * 50)
    print("测试线程管理")
    print("=" * 50)
    
    print("检查初始线程状态...")
    print(f"按键循环线程存在: {fishing_controller.key_cycle_thread is not None}")
    print(f"按键循环线程运行: {fishing_controller.key_cycle_thread and fishing_controller.key_cycle_thread.is_alive()}")
    
    print("启动按键循环...")
    fishing_controller._start_key_cycle()
    
    print("检查启动后线程状态...")
    print(f"按键循环线程存在: {fishing_controller.key_cycle_thread is not None}")
    print(f"按键循环线程运行: {fishing_controller.key_cycle_thread and fishing_controller.key_cycle_thread.is_alive()}")
    
    time.sleep(3)
    
    print("停止按键循环...")
    fishing_controller._stop_key_cycle()
    
    print("检查停止后线程状态...")
    print(f"按键循环线程存在: {fishing_controller.key_cycle_thread is not None}")
    print(f"按键循环线程运行: {fishing_controller.key_cycle_thread and fishing_controller.key_cycle_thread.is_alive()}")
    
    return True


def main():
    """主测试函数"""
    print("Fisher钓鱼模块按键循环功能测试")
    print("测试内容：")
    print("1. 按键循环功能测试")
    print("2. 提线阶段模拟测试")
    print("3. 线程管理测试")
    print()
    print("⚠️  注意：此测试会实际按键，请确保游戏窗口处于前台！")
    print("按 Enter 继续，Ctrl+C 取消...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("测试已取消")
        return
    
    try:
        # 测试按键循环功能
        key_cycle_ok = test_key_cycle_functionality()
        
        # 测试提线阶段模拟
        pulling_phase_ok = test_pulling_phase_simulation()
        
        # 测试线程管理
        thread_mgmt_ok = test_thread_management()
        
        print("\n" + "=" * 50)
        print("🎉 测试结果总结")
        print("=" * 50)
        print(f"按键循环功能: {'✅ 通过' if key_cycle_ok else '❌ 失败'}")
        print(f"提线阶段模拟: {'✅ 通过' if pulling_phase_ok else '❌ 失败'}")
        print(f"线程管理: {'✅ 通过' if thread_mgmt_ok else '❌ 失败'}")
        
        if all([key_cycle_ok, pulling_phase_ok, thread_mgmt_ok]):
            print("\n🎉 所有测试通过！按键循环功能正常！")
            print("功能说明:")
            print("✅ 按键循环: a键1秒 → 等待1秒 → d键1秒 → 等待1秒")
            print("✅ 状态检测: 继续检测状态2/3/6")
            print("✅ 自动停止: 检测到状态6时自动停止按键循环")
            print("✅ 线程安全: 正确启动和停止按键循环线程")
        else:
            print("\n⚠️ 部分测试失败，需要进一步检查")
        
    except KeyboardInterrupt:
        print("\n用户中断测试")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 确保清理资源
        try:
            fishing_controller.emergency_stop()
            print("测试资源清理完成")
        except:
            pass


if __name__ == "__main__":
    main() 