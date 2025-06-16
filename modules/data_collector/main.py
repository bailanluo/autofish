"""
数据采集工具主程序 v2.2 - 重构版
架构优化：分离UI和业务逻辑，提高代码可维护性
"""

import tkinter as tk
import sys
import os
import ctypes
from typing import Dict

# 添加主项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from modules.logger import setup_logger

# 导入模块 - 支持直接运行和模块导入
try:
    from .ui_manager import UIManager
    from .business_logic import BusinessLogic
    from .config_manager import DataCollectorConfig
    from .admin_utils import request_admin_if_needed, get_admin_status_message
except ImportError:
    from ui_manager import UIManager
    from business_logic import BusinessLogic
    from config_manager import DataCollectorConfig
    from admin_utils import request_admin_if_needed, get_admin_status_message


class DataCollectorApp:
    """数据采集工具主应用程序 - 重构版（UI与业务逻辑分离）"""
    
    def __init__(self):
        """初始化应用程序"""
        self.logger = setup_logger('DataCollectorApp')
        self.logger.info("启动数据采集工具 v2.2 (重构版)")
        
        # 设置DPI感知，修复高DPI显示器界面缩放问题
        self._set_dpi_awareness()
        
        # 检查管理员权限
        config = DataCollectorConfig()
        admin_requested = request_admin_if_needed(config)
        
        # 记录管理员状态
        admin_status = get_admin_status_message()
        if admin_requested:
            self.logger.info(admin_status)
        else:
            self.logger.warning(admin_status)
        
        # 创建主窗口
        self.root = tk.Tk()
        
        # 初始化业务逻辑管理器
        self.business = BusinessLogic(self.root)
        
        # 初始化UI管理器
        self.ui_manager = UIManager(self.root, self.business)
        
        # 设置相互引用
        self.business.set_ui_manager(self.ui_manager)
        
        # 创建界面
        self.ui_manager.create_main_ui()
        
        # 初始化数据和检查
        self.business.update_statistics()
        self.business.initialize_permissions_check()
        
        self.logger.info("应用程序初始化完成")
    
    def _set_dpi_awareness(self):
        """设置程序DPI感知，修复高DPI显示器界面缩放问题"""
        try:
            # 设置为系统DPI感知（仅Windows）
            if sys.platform == "win32":
                ctypes.windll.user32.SetProcessDPIAware()
                self.logger.info("已设置DPI感知，修复高DPI显示问题")
        except Exception as e:
            self.logger.warning(f"设置DPI感知失败: {e}")
    
    def run(self):
        """运行应用程序"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        """程序关闭处理"""
        try:
            self.business.cleanup()
            self.root.destroy()
        except Exception as e:
            self.logger.error(f"关闭程序异常: {e}")


def main():
    """主函数"""
    try:
        app = DataCollectorApp()
        app.run()
    except Exception as e:
        print(f"程序启动失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 