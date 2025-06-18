"""
简单的状态检测测试脚本
用于测试模型检测功能

作者: AutoFish Team
版本: v1.0.9
创建时间: 2025-01-17
"""

import sys
import os
from pathlib import Path
import time

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from modules.fisher.config import fisher_config
from modules.fisher.model_detector import model_detector


def test_model_detection():
    """测试模型检测功能"""
    print("=" * 50)
    print("🤖 模型检测测试")
    print("=" * 50)
    
    if not model_detector.is_initialized:
        print("❌ 模型检测器未初始化")
        return
    
    print("✅ 模型检测器已初始化")
    print(f"📊 检测间隔: {fisher_config.model.detection_interval}秒")
    print(f"🎯 置信度阈值: {fisher_config.model.confidence_threshold}")
    
    print("\n🔍 开始连续检测所有状态...")
    print("🔑 按Ctrl+C停止测试")
    print("-" * 50)
    
    detection_count = 0
    state_counts = {}
    
    try:
        while True:
            detection_count += 1
            
            # 检测所有状态
            result = model_detector.detect_multiple_states([0, 1, 2, 3, 6])
            
            if result:
                state = result['state']
                confidence = result['confidence']
                
                # 统计状态出现次数
                state_counts[state] = state_counts.get(state, 0) + 1
                
                print(f"✅ 检测到状态 {state} (置信度: {confidence:.2f}) - 第{detection_count}次检测")
            else:
                print(f"❌ 无法检测到任何状态 - 第{detection_count}次检测")
            
            # 每100次检测输出统计信息
            if detection_count % 100 == 0:
                print(f"\n📊 统计信息（前{detection_count}次检测）:")
                for state, count in sorted(state_counts.items()):
                    percentage = (count / detection_count) * 100
                    print(f"   状态{state}: {count}次 ({percentage:.1f}%)")
                print("-" * 50)
            
            time.sleep(fisher_config.model.detection_interval)
    
    except KeyboardInterrupt:
        print(f"\n🛑 测试结束")
        print(f"📊 最终统计（共{detection_count}次检测）:")
        
        if state_counts:
            for state, count in sorted(state_counts.items()):
                percentage = (count / detection_count) * 100
                print(f"   状态{state}: {count}次 ({percentage:.1f}%)")
        else:
            print("   没有检测到任何状态")


if __name__ == "__main__":
    test_model_detection() 