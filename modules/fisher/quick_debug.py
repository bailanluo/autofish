#!/usr/bin/env python3
"""
Fisher钓鱼模块 - 快速调试脚本
立即测试模型检测功能，输出详细信息

作者: AutoFish Team
版本: v1.0.10
创建时间: 2025-01-17
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from modules.fisher.config import fisher_config
from modules.fisher.model_detector import model_detector

def quick_test():
    """快速测试模型检测功能"""
    print("🚀 Fisher模型快速检测测试")
    print("=" * 50)
    
    # 检查初始化状态
    print(f"🔧 模型检测器状态: {'✅初始化完成' if model_detector.is_initialized else '❌未初始化'}")
    print(f"🔧 模型对象状态: {'✅正常' if model_detector.model is not None else '❌空对象'}")
    print(f"🔧 置信度阈值: {fisher_config.model.confidence_threshold}")
    
    if not model_detector.is_initialized:
        print("❌ 模型未初始化，无法进行测试")
        return
    
    print("\n📸 开始屏幕截图...")
    image = model_detector.capture_screen()
    
    if image is None:
        print("❌ 屏幕截图失败")
        return
    
    print(f"✅ 屏幕截图成功，尺寸: {image.shape}")
    
    # 测试不同置信度阈值
    thresholds = [0.01, 0.1, 0.3, 0.5]
    
    for thresh in thresholds:
        print(f"\n🔍 测试置信度阈值: {thresh}")
        try:
            results = model_detector.model(image, conf=thresh, verbose=False)
            
            if len(results) > 0 and len(results[0].boxes) > 0:
                boxes = results[0].boxes
                confidences = boxes.conf.cpu().numpy()
                classes = boxes.cls.cpu().numpy().astype(int)
                
                print(f"   📊 检测到 {len(classes)} 个目标:")
                for i, (cls, conf) in enumerate(zip(classes, confidences)):
                    state_name = model_detector.state_names.get(cls, f"未知状态_{cls}")
                    target_mark = "🎯" if cls in [0, 1, 2, 3, 6] else "❓"
                    print(f"      {target_mark} [{i+1}] 状态{cls}({state_name}) - 置信度:{conf:.4f}")
            else:
                print(f"   ❌ 无检测结果")
                
        except Exception as e:
            print(f"   💥 检测异常: {e}")
    
    # 使用标准检测方法
    print(f"\n🏆 标准检测方法测试:")
    standard_result = model_detector.detect_states()
    if standard_result:
        print(f"   ✅ 检测到: 状态{standard_result['state']}({standard_result['state_name']}) - 置信度:{standard_result['confidence']:.4f}")
    else:
        print(f"   ❌ 无检测结果")
    
    print(f"\n🎉 快速测试完成")

if __name__ == "__main__":
    try:
        quick_test()
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc() 