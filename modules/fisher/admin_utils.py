"""
Fisher钓鱼模块管理员权限工具
负责检查和提升管理员权限，确保程序能够控制键鼠

作者: AutoFish Team
版本: v1.0.1
创建时间: 2024-12-28
"""

import os
import sys
import ctypes
import subprocess
from typing import Optional


def is_admin() -> bool:
    """
    检查当前程序是否以管理员身份运行
    
    Returns:
        bool: 是否为管理员权限
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_as_admin(script_path: Optional[str] = None) -> bool:
    """
    以管理员身份重新启动程序
    
    Args:
        script_path: 脚本路径，默认为当前脚本
        
    Returns:
        bool: 是否成功启动
    """
    if script_path is None:
        script_path = sys.argv[0]
    
    try:
        # 获取Python解释器路径
        python_exe = sys.executable
        
        # 构建启动参数
        params = f'"{python_exe}" "{script_path}"'
        
        # 添加命令行参数
        if len(sys.argv) > 1:
            params += " " + " ".join(f'"{arg}"' for arg in sys.argv[1:])
        
        print(f"正在以管理员身份重新启动程序...")
        print(f"启动命令: {params}")
        
        # 使用ShellExecute以管理员身份启动，隐藏控制台窗口
        result = ctypes.windll.shell32.ShellExecuteW(
            None,           # hwnd
            "runas",        # lpOperation (以管理员身份运行)
            python_exe,     # lpFile
            f'"{script_path}"' + (" " + " ".join(f'"{arg}"' for arg in sys.argv[1:]) if len(sys.argv) > 1 else ""),  # lpParameters
            None,           # lpDirectory
            0               # nShowCmd (SW_HIDE - 隐藏窗口)
        )
        
        # 如果成功启动，返回True
        if result > 32:  # ShellExecute成功返回值大于32
            print("管理员权限程序启动成功")
            return True
        else:
            print(f"管理员权限程序启动失败，错误代码: {result}")
            return False
            
    except Exception as e:
        print(f"以管理员身份启动失败: {e}")
        return False


def check_and_elevate_privileges() -> bool:
    """
    检查管理员权限，如果没有则自动提升
    
    Returns:
        bool: True表示已有管理员权限，False表示需要退出当前进程
    """
    if is_admin():
        print("✅ 已获得管理员权限")
        return True
    else:
        print("⚠️  当前程序未以管理员身份运行")
        print("Fisher钓鱼模块需要管理员权限才能在游戏中控制键鼠")
        print("正在尝试以管理员身份重新启动...")
        
        # 尝试以管理员身份重新启动
        if run_as_admin():
            print("请在新打开的管理员权限窗口中继续使用程序")
            print("当前窗口将自动关闭...")
            return False
        else:
            print("❌ 无法获取管理员权限")
            print("请手动以管理员身份运行程序:")
            print("1. 右键点击程序图标")
            print("2. 选择'以管理员身份运行'")
            print("3. 或使用管理员权限的命令提示符启动")
            return False


def create_admin_shortcut(target_path: str, shortcut_name: str = "Fisher钓鱼模块 (管理员)") -> bool:
    """
    创建以管理员身份运行的快捷方式
    
    Args:
        target_path: 目标程序路径
        shortcut_name: 快捷方式名称
        
    Returns:
        bool: 是否创建成功
    """
    try:
        import winshell
        from win32com.client import Dispatch
        
        # 获取桌面路径
        desktop = winshell.desktop()
        shortcut_path = os.path.join(desktop, f"{shortcut_name}.lnk")
        
        # 创建快捷方式
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = sys.executable
        shortcut.Arguments = f'"{target_path}"'
        shortcut.WorkingDirectory = os.path.dirname(target_path)
        shortcut.IconLocation = sys.executable
        shortcut.save()
        
        # 设置以管理员身份运行
        # 注意：这需要修改快捷方式的属性，通常需要用户手动设置
        print(f"快捷方式已创建: {shortcut_path}")
        print("请右键点击快捷方式 -> 属性 -> 高级 -> 勾选'用管理员身份运行'")
        
        return True
        
    except ImportError:
        print("创建快捷方式需要安装 pywin32 和 winshell")
        print("pip install pywin32 winshell")
        return False
    except Exception as e:
        print(f"创建快捷方式失败: {e}")
        return False


def show_admin_help():
    """显示管理员权限帮助信息"""
    print("\n" + "=" * 60)
    print("🔐 管理员权限说明")
    print("=" * 60)
    print("Fisher钓鱼模块需要管理员权限的原因:")
    print("• 在游戏全屏模式下控制鼠标和键盘")
    print("• 访问游戏窗口进行屏幕截取")
    print("• 模拟按键输入到游戏程序")
    print("• 绕过某些游戏的输入保护机制")
    print()
    print("获取管理员权限的方法:")
    print("1. 右键点击程序 -> '以管理员身份运行'")
    print("2. 使用管理员权限的命令提示符启动")
    print("3. 创建管理员权限的快捷方式")
    print("4. 修改程序属性 -> 兼容性 -> '以管理员身份运行此程序'")
    print("=" * 60)


def test_admin_privileges():
    """测试管理员权限功能"""
    print("测试管理员权限检查...")
    
    if is_admin():
        print("✅ 当前已有管理员权限")
        print("可以正常控制键鼠和访问游戏窗口")
    else:
        print("❌ 当前没有管理员权限")
        print("可能无法在游戏中正常工作")
        
        # 询问是否尝试提升权限
        try:
            choice = input("是否尝试以管理员身份重新启动? (y/n): ").lower().strip()
            if choice in ['y', 'yes', '是']:
                if run_as_admin():
                    print("请在新窗口中继续...")
                    return False
                else:
                    print("权限提升失败")
            else:
                show_admin_help()
        except KeyboardInterrupt:
            print("\n用户取消操作")
    
    return True


if __name__ == "__main__":
    # 测试功能
    test_admin_privileges() 