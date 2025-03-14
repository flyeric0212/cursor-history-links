# Cursor 工具集一键执行脚本 - PowerShell 版本
# 适配 PyInstaller 打包的可执行文件

# 设置颜色
$colors = @{
    Red     = [System.ConsoleColor]::Red
    Green   = [System.ConsoleColor]::Green
    Yellow  = [System.ConsoleColor]::Yellow
    Blue    = [System.ConsoleColor]::Cyan
    Cyan    = [System.ConsoleColor]::Cyan
    Default = [System.ConsoleColor]::White
}

# GitHub 仓库信息
$repoOwner = "flyeric0212"
$repoName = "cursor-pro-free"

# 版本信息
$version = "1.0.0"
$tag = "v$version"

# 临时文件路径
$tmpDir = Join-Path $env:TEMP "cursor-tools"
if (-not (Test-Path $tmpDir)) {
    New-Item -ItemType Directory -Path $tmpDir | Out-Null
}

# 可执行文件信息
$exeUrl = "https://github.com/$repoOwner/$repoName/releases/download/$tag/cursor-tools-windows-x64.exe"
$exePath = Join-Path $tmpDir "cursor-tools-windows-x64.exe"

# 彩色输出函数
function Write-ColorOutput {
    param (
        [string]$message,
        [System.ConsoleColor]$color = $colors.Default
    )

    $oldColor = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $color
    Write-Output $message
    $host.UI.RawUI.ForegroundColor = $oldColor
}

# 下载可执行文件
function Download-Executable {
    Write-ColorOutput "正在下载 Cursor 工具集..." $colors.Blue

    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $exeUrl -OutFile $exePath -UseBasicParsing

        if (Test-Path $exePath) {
            Write-ColorOutput "✅ 下载成功" $colors.Green
            return $true
        } else {
            Write-ColorOutput "❌ 下载失败" $colors.Red
            return $false
        }
    } catch {
        Write-ColorOutput "❌ 下载失败: $_" $colors.Red
        return $false
    }
}

# 检查更新
function Check-Update {
    Write-ColorOutput "检查更新..." $colors.Blue

    try {
        $latestRelease = Invoke-RestMethod -Uri "https://api.github.com/repos/$repoOwner/$repoName/releases/latest" -UseBasicParsing
        $latestVersion = $latestRelease.tag_name -replace 'v', ''

        if ($latestVersion -ne $version) {
            Write-ColorOutput "⚠️ 发现新版本: $latestVersion (当前版本: $version)" $colors.Yellow
            Write-ColorOutput "⚠️ 请访问 https://github.com/$repoOwner/$repoName/releases/latest 获取最新版本" $colors.Yellow
        } else {
            Write-ColorOutput "✅ 当前已是最新版本" $colors.Green
        }
    } catch {
        Write-ColorOutput "⚠️ 无法检查更新: $_" $colors.Yellow
    }
}

# 显示菜单
function Show-Menu {
    Write-ColorOutput "======================================" $colors.Cyan
    Write-ColorOutput "       Cursor 工具集一键执行脚本       " $colors.Cyan
    Write-ColorOutput "======================================" $colors.Cyan
    Write-ColorOutput "请选择要执行的操作:" $colors.Yellow
    Write-ColorOutput "1. 重置设备 ID (解决试用限制)" $colors.Blue
    Write-ColorOutput "2. 禁用自动更新 (锁定版本)" $colors.Blue
    Write-ColorOutput "3. 恢复自动更新" $colors.Blue
    Write-ColorOutput "0. 退出" $colors.Blue
    Write-ColorOutput "======================================" $colors.Cyan

    $choice = Read-Host "请输入选项 [0-3]"
    return $choice
}

# 执行工具集命令
function Run-Tool {
    param (
        [string]$command,
        [string]$description
    )

    Write-ColorOutput "执行: $description" $colors.Blue

    if (Test-Path $exePath) {
        if ($command) {
            & $exePath $command
        } else {
            & $exePath
        }
    } else {
        Write-ColorOutput "⚠️ 可执行文件不存在，尝试下载..." $colors.Yellow
        if (Download-Executable) {
            if ($command) {
                & $exePath $command
            } else {
                & $exePath
            }
        } else {
            Write-ColorOutput "❌ 无法获取工具集" $colors.Red
        }
    }
}

# 主函数
function Main {
    # 检查更新
    Check-Update

    # 显示菜单并获取用户选择
    $choice = Show-Menu

    # 根据用户选择执行相应操作
    switch ($choice) {
        "1" { Run-Tool "reset" "重置设备 ID" }
        "2" { Run-Tool "disable-update" "禁用自动更新" }
        "3" { Run-Tool "enable-update" "恢复自动更新" }
        "0" { Write-ColorOutput "感谢使用，再见！" $colors.Green }
        default { Write-ColorOutput "❌ 无效的选项" $colors.Red }
    }
}

# 执行主函数
Main