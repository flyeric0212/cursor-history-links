@echo off
REM Cursor 工具集一键执行脚本 - Windows 版本
REM 适配 PyInstaller 打包的可执行文件

setlocal enabledelayedexpansion

REM 设置颜色
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "CYAN=[96m"
set "NC=[0m"

REM GitHub 仓库信息
set "REPO_OWNER=flyeric0212"
set "REPO_NAME=cursor-pro-free"

REM 版本信息
set "VERSION=1.0.0"
set "TAG=v%VERSION%"

REM 临时文件路径
set "TMP_DIR=%TEMP%\cursor-tools"
if not exist "%TMP_DIR%" mkdir "%TMP_DIR%"

REM 可执行文件信息
set "EXE_URL=https://github.com/%REPO_OWNER%/%REPO_NAME%/releases/download/%TAG%/cursor-tools-windows-x64.exe"
set "EXE_PATH=%TMP_DIR%\cursor-tools-windows-x64.exe"

REM 下载可执行文件
:download_executable
echo %BLUE%正在下载 Cursor 工具集...%NC%

REM 使用 PowerShell 下载文件
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%EXE_URL%' -OutFile '%EXE_PATH%'}" > nul 2>&1

if exist "%EXE_PATH%" (
    echo %GREEN%✅ 下载成功%NC%
) else (
    echo %RED%❌ 下载失败%NC%
    goto :eof
)

REM 显示菜单
:show_menu
echo %CYAN%======================================%NC%
echo %CYAN%       Cursor 工具集一键执行脚本       %NC%
echo %CYAN%======================================%NC%
echo %YELLOW%请选择要执行的操作:%NC%
echo %BLUE%1. 重置设备 ID (解决试用限制)%NC%
echo %BLUE%2. 禁用自动更新 (锁定版本)%NC%
echo %BLUE%3. 恢复自动更新%NC%
echo %BLUE%0. 退出%NC%
echo %CYAN%======================================%NC%
set /p choice=%YELLOW%请输入选项 [0-3]: %NC%

REM 根据用户选择执行相应操作
if "%choice%"=="1" (
    call :run_tool reset "重置设备 ID"
) else if "%choice%"=="2" (
    call :run_tool disable-update "禁用自动更新"
) else if "%choice%"=="3" (
    call :run_tool enable-update "恢复自动更新"
) else if "%choice%"=="0" (
    echo %GREEN%感谢使用，再见！%NC%
) else (
    echo %RED%❌ 无效的选项%NC%
)

goto :eof

REM 执行工具集命令
:run_tool
echo %BLUE%执行: %~2%NC%

if exist "%EXE_PATH%" (
    if "%~1"=="" (
        "%EXE_PATH%"
    ) else (
        "%EXE_PATH%" %~1
    )
) else (
    echo %YELLOW%⚠️ 可执行文件不存在，尝试下载...%NC%
    goto :download_executable
)

goto :eof