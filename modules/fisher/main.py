"""
Fisher钓鱼模块主程序
负责初始化和启动钓鱼模块

作者: AutoFish Team
版本: v1.0.1
创建时间: 2024-12-28
更新时间: 2025-01-17
修复历史: v1.0.1 - 集成统一日志系统
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入统一日志系统
from modules.logger import setup_logger

# 修复相对导入问题 - 使用绝对导入
from modules.fisher.config import fisher_config
from modules.fisher.model_detector import model_detector
from modules.fisher.admin_utils import is_admin, check_and_elevate_privileges

# 设置日志记录器
logger = setup_logger('fisher_main')

# 版本信息
APP_VERSION = "v1.0.30"
APP_NAME = "Fisher钓鱼模块"

def check_dependencies() -> bool:
    """
    检查系统依赖项
    
    Returns:
        bool: 依赖项是否完整
    """
    logger.info("检查系统依赖...")
    
    # 检查关键路径
    model_path = fisher_config.get_model_path()
    if not Path(model_path).exists():
        logger.error("关键路径验证失败")
        return False
    
    # 检查模型检测器初始化状态
    if not model_detector.is_initialized:
        logger.error("模型检测器初始化失败")
        return False
    
    logger.info("系统依赖检查通过")
    return True

def main():
    """主函数"""
    try:
        logger.info("=" * 50)
        logger.info("Fisher钓鱼模块 v1.0.30")
        logger.info("智能钓鱼辅助工具 - 调试日志增强版")
        logger.info("=" * 50)
        
        # 检查管理员权限
        logger.info("检查管理员权限...")
        if not check_and_elevate_privileges():
            logger.warning("未获得管理员权限，程序可能无法正常工作")
            return
        
        # 检查依赖项
        if not check_dependencies():
            logger.error("依赖项检查失败，请检查配置")
            input("按回车键退出...")
            return
        
        logger.info("启动Fisher钓鱼模块...")
        
        # 优先使用美化UI，如果失败则回退到原UI
        try:
            from modules.fisher.ui_simple import fisher_ui
            logger.info("使用美化UI界面")
        except ImportError as e:
            logger.warning(f"美化UI加载失败，回退到原UI: {e}")
            from modules.fisher.ui import fisher_ui
        
        # 启动UI界面
        fisher_ui.run()
        
    except KeyboardInterrupt:
        logger.info("\n用户中断程序")
    except Exception as e:
        logger.error(f"程序运行异常: {e}")
        import traceback
        traceback.print_exc()
        # 如果是控制台环境，等待用户确认；如果是无窗口环境，直接退出
        if sys.stdout.isatty():
            input("按回车键退出...")
    finally:
        logger.info("Fisher钓鱼模块已退出")
        # 确保程序彻底退出
        try:
            import tkinter as tk
            # 如果有tkinter窗口，强制退出
            root = tk.Tk()
            root.quit()
            root.destroy()
        except:
            pass
        sys.exit(0)

if __name__ == "__main__":
    main() 