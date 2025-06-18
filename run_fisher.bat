@echo off
:: AutoFish钓鱼模块启动脚本
:: 使用conda环境NLP2运行钓鱼程序
chcp 65001 >nul

:: 检查是否以管理员身份运行
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 正在请求管理员权限...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: 设置工作目录为项目根目录
cd /d "F:\practice\Python\autofish"

echo ===================================
echo AutoFish v1.0.10 钓鱼模块启动器
echo 智能化钓鱼辅助工具
echo ===================================
echo.

:: 设置Anaconda路径
set CONDA_PATH=D:\anaconda
set ENV_NAME=NLP2

:: 检查Anaconda是否存在
if not exist "%CONDA_PATH%\Scripts\conda.exe" (
    echo 错误: 未找到Anaconda安装目录: %CONDA_PATH%
    echo 请检查Anaconda安装路径是否正确
    pause
    exit /b 1
)

:: 检查环境是否存在
if not exist "%CONDA_PATH%\envs\%ENV_NAME%" (
    echo 错误: 未找到conda环境: %ENV_NAME%
    echo 请确认环境名称是否正确，或使用以下命令创建环境:
    echo conda create -n %ENV_NAME% python=3.8
    pause
    exit /b 1
)

echo 正在激活conda环境: %ENV_NAME%...
:: 初始化conda
call "%CONDA_PATH%\Scripts\activate.bat" "%CONDA_PATH%"

:: 激活指定环境
call conda activate %ENV_NAME%
if errorlevel 1 (
    echo 错误: 无法激活conda环境 %ENV_NAME%
    pause
    exit /b 1
)

echo 环境激活成功！
echo 当前工作目录: %CD%
echo.

:: 显示快捷键提示
echo ===================================
echo 🎣 Fisher钓鱼模块快捷键:
echo   Ctrl+Alt+S  : 开始钓鱼
echo   Ctrl+Alt+X  : 停止钓鱼  
echo   Ctrl+Alt+Q  : 紧急停止
echo ===================================
echo.

:: 运行钓鱼模块
echo 启动Fisher钓鱼模块...
echo ===================================
python -W ignore::RuntimeWarning -m modules.fisher.main

:: 如果程序异常退出，显示错误信息
if errorlevel 1 (
    echo.
    echo ===================================
    echo 程序异常退出，错误代码: %errorlevel%
    echo 请检查以下可能的问题:
    echo 1. 游戏是否正在运行且处于钓鱼界面
    echo 2. 模型文件是否存在: runs/fishing_model_latest.pt
    echo 3. 是否有管理员权限
    echo 4. GPU/CUDA是否正常工作
    echo ===================================
)

echo.
echo 🎣 Fisher钓鱼模块已退出
echo 按任意键关闭窗口...
pause 