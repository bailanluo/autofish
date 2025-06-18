"""
Fisher钓鱼模块主程序入口
智能钓鱼辅助工具的核心模块

作者: AutoFish Team
版本: v1.0
创建时间: 2024-12-28
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from modules.fisher.ui import fisher_ui
from modules.fisher.config import fisher_config
from modules.fisher.model_detector import model_detector
from modules.fisher.admin_utils import check_and_elevate_privileges


def check_dependencies() -> bool:
    """
    检查依赖项是否满足
    
    Returns:
        bool: 依赖项是否满足
    """
    print("检查系统依赖...")
    
    # 检查关键路径
    if not fisher_config.validate_paths():
        print("关键路径验证失败")
        return False
    
    # 检查模型初始化
    if not model_detector.is_initialized:
        print("模型检测器初始化失败")
        return False
    
    print("系统依赖检查通过")
    return True


def main():
    """主函数"""
    print("=" * 50)
    print("Fisher钓鱼模块 v1.0.12")
    print("智能钓鱼辅助工具")
    print("=" * 50)
    
    try:
        # 首先检查管理员权限
        print("检查管理员权限...")
        if not check_and_elevate_privileges():
            # 如果返回False，说明正在以管理员身份重新启动，当前进程应该退出
            return
        
        # 检查依赖项
        if not check_dependencies():
            print("依赖项检查失败，请检查配置")
            input("按任意键退出...")
            return
        
        print("启动Fisher钓鱼模块...")
        
        # 启动UI界面
        fisher_ui.run()
        
    except KeyboardInterrupt:
        print("\n用户中断程序")
    except Exception as e:
        print(f"程序运行异常: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("Fisher钓鱼模块已退出")


if __name__ == "__main__":
    main() 