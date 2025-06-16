@echo off
:: 以管理员权限运行批处理文件
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo 请求管理员权限...
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    if exist "%temp%\getadmin.vbs" ( del "%temp%\getadmin.vbs" )
    pushd "%CD%"
    CD /D "%~dp0"

:: 设置编码为UTF-8
chcp 65001 > nul

:: 输出启动信息
echo ===============================================
echo            AutoFish 钓鱼程序启动器
echo ===============================================
echo.
echo 正在启动钓鱼程序，请稍候...
echo.

:: 启动Python程序
python start_autofish.py --log-level INFO

:: 如果程序异常退出，暂停显示错误信息
if %errorlevel% neq 0 (
    echo.
    echo 程序异常退出，错误代码: %errorlevel%
    echo 请查看logs目录下的日志文件了解详细信息
    pause
) 