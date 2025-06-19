@echo off
REM Fisher钓鱼模块启动脚本 - Conda环境版本
REM 使用conda环境启动main.py，批处理窗口自动关闭

cd /d "%~dp0"

REM 设置Anaconda路径和环境名
set CONDA_PATH=D:\anaconda
set ENV_NAME=NLP2

REM 检查Anaconda是否存在
if not exist "%CONDA_PATH%\Scripts\conda.exe" (
    echo 错误: 未找到Anaconda安装目录: %CONDA_PATH%
    echo 请检查Anaconda安装路径是否正确
    pause
    exit /b 1
)

REM 检查环境是否存在
if not exist "%CONDA_PATH%\envs\%ENV_NAME%" (
    echo 错误: 未找到conda环境: %ENV_NAME%
    echo 请确认环境名称是否正确
    pause
    exit /b 1
)

REM 启动程序，批处理窗口立即关闭
start /b "" "%CONDA_PATH%\envs\%ENV_NAME%\python.exe" modules\fisher\main.py

REM 批处理脚本立即退出，窗口关闭
exit /b 0 