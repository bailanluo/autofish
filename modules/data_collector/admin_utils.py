"""
管理员权限工具模块
提供管理员权限检查和程序重启功能
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
        bool: True表示以管理员身份运行，False表示普通用户
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_as_admin(script_path: Optional[str] = None) -> bool:
    """
    以管理员身份重新启动程序
    
    Args:
        script_path: 要运行的脚本路径，默认为当前脚本
        
    Returns:
        bool: True表示成功启动，False表示失败
    """
    try:
        if script_path is None:
            script_path = sys.argv[0]
        
        # 构建命令行参数
        params = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else ''
        
        # 使用ShellExecute以管理员身份运行
        result = ctypes.windll.shell32.ShellExecuteW(
            None, 
            "runas", 
            sys.executable, 
            f'"{script_path}" {params}', 
            None, 
            1  # SW_SHOWNORMAL
        )
        
        # 如果成功启动，退出当前进程
        if result > 32:  # ShellExecute成功返回值大于32
            return True
        else:
            return False
            
    except Exception as e:
        print(f"以管理员身份启动失败: {e}")
        return False


def request_admin_if_needed(config_manager) -> bool:
    """
    根据配置检查是否需要管理员权限，如果需要且当前不是管理员则请求提升权限
    
    Args:
        config_manager: 配置管理器实例
        
    Returns:
        bool: True表示已经是管理员或成功提升权限，False表示用户拒绝或失败
    """
    # 检查配置是否要求管理员权限
    if not config_manager.get_run_as_admin():
        return True  # 不需要管理员权限
    
    # 检查当前是否已经是管理员
    if is_admin():
        return True  # 已经是管理员
    
    # 需要管理员权限但当前不是管理员，尝试提升权限
    print("程序配置为以管理员身份运行，正在请求管理员权限...")
    
    if run_as_admin():
        # 成功启动管理员版本，退出当前进程
        sys.exit(0)
    else:
        # 用户拒绝或启动失败
        print("无法获取管理员权限，程序将以普通用户身份运行")
        print("某些功能（如全局热键）可能受限")
        return False


def get_admin_status_message() -> str:
    """
    获取当前管理员状态的描述信息
    
    Returns:
        str: 状态描述信息
    """
    if is_admin():
        return "✅ 当前以管理员身份运行"
    else:
        return "⚠️ 当前以普通用户身份运行，某些功能可能受限"


def create_admin_shortcut(target_path: str, shortcut_path: str, description: str = "") -> bool:
    """
    创建以管理员身份运行的快捷方式
    
    Args:
        target_path: 目标程序路径
        shortcut_path: 快捷方式保存路径
        description: 快捷方式描述
        
    Returns:
        bool: 创建成功返回True，失败返回False
    """
    try:
        import win32com.client
        
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = target_path
        shortcut.Description = description
        shortcut.WorkingDirectory = os.path.dirname(target_path)
        
        # 设置以管理员身份运行（需要修改快捷方式文件）
        shortcut.Save()
        
        # 使用PowerShell设置管理员权限标志
        ps_command = f'''
        $bytes = [System.IO.File]::ReadAllBytes("{shortcut_path}")
        $bytes[0x15] = $bytes[0x15] -bor 0x20
        [System.IO.File]::WriteAllBytes("{shortcut_path}", $bytes)
        '''
        
        subprocess.run(["powershell", "-Command", ps_command], 
                      capture_output=True, text=True, check=True)
        
        return True
        
    except Exception as e:
        print(f"创建管理员快捷方式失败: {e}")
        return False 