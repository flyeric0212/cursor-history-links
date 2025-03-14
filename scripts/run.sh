#!/bin/bash
# Cursor 工具集一键执行脚本
# 支持 macOS, Linux 和 Windows (通过 Git Bash 或 WSL)
# 适配 PyInstaller 打包的可执行文件版本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # 无颜色

# GitHub 仓库信息
REPO_OWNER="flyeric0212"
REPO_NAME="cursor-pro-free"

# 版本信息
VERSION="1.0.0"
TAG="v$VERSION"

# 临时文件路径
TMP_DIR="/tmp/cursor-tools"
mkdir -p "$TMP_DIR"

# 检测操作系统和架构
detect_platform() {
  local os arch platform

  # 检测操作系统
  case "$(uname -s)" in
    Darwin*)
      os="macos"
      # 检测 macOS 架构
      if [ "$(uname -m)" = "arm64" ]; then
        arch="arm64"  # Apple Silicon
      else
        arch="x64"    # Intel
      fi
      ;;
    Linux*)
      if grep -q Microsoft /proc/version 2>/dev/null; then
        os="wsl"
      else
        os="linux"
      fi
      arch="x64"  # 目前只支持 x64 Linux
      ;;
    MINGW*|MSYS*|CYGWIN*)
      os="windows"
      arch="x64"  # 目前只支持 x64 Windows
      ;;
    *)
      os="unknown"
      arch="unknown"
      ;;
  esac

  # 返回平台标识
  echo "${os}-${arch}"
}

# 获取可执行文件 URL
get_executable_url() {
  local platform=$1
  local base_url="https://github.com/$REPO_OWNER/$REPO_NAME/releases/download/$TAG"

  case "$platform" in
    macos-arm64)
      echo "$base_url/cursor-tools-macos-arm64"
      ;;
    macos-x64)
      echo "$base_url/cursor-tools-macos-x64"
      ;;
    linux-x64|wsl-x64)
      echo "$base_url/cursor-tools-linux-x64"
      ;;
    windows-x64)
      echo "$base_url/cursor-tools-windows-x64.exe"
      ;;
    *)
      echo ""
      ;;
  esac
}

# 获取可执行文件本地路径
get_executable_path() {
  local platform=$1

  case "$platform" in
    macos-arm64)
      echo "$TMP_DIR/cursor-tools-macos-arm64"
      ;;
    macos-x64)
      echo "$TMP_DIR/cursor-tools-macos-x64"
      ;;
    linux-x64|wsl-x64)
      echo "$TMP_DIR/cursor-tools-linux-x64"
      ;;
    windows-x64)
      echo "$TMP_DIR/cursor-tools-windows-x64.exe"
      ;;
    *)
      echo ""
      ;;
  esac
}

# 下载可执行文件
download_executable() {
  local platform=$1
  local url=$(get_executable_url "$platform")
  local path=$(get_executable_path "$platform")

  if [ -z "$url" ] || [ -z "$path" ]; then
    echo -e "${RED}❌ 不支持的平台: $platform${NC}"
    return 1
  fi

  echo -e "${BLUE}正在下载 Cursor 工具集...${NC}"

  # 下载可执行文件
  if command -v curl >/dev/null 2>&1; then
    curl -L -s -o "$path" "$url"
  elif command -v wget >/dev/null 2>&1; then
    wget -q -O "$path" "$url"
  else
    echo -e "${RED}❌ 需要 curl 或 wget 来下载文件${NC}"
    return 1
  fi

  # 设置执行权限
  chmod +x "$path"

  if [ -f "$path" ]; then
    echo -e "${GREEN}✅ 下载成功${NC}"
    return 0
  else
    echo -e "${RED}❌ 下载失败${NC}"
    return 1
  fi
}

# 显示菜单
show_menu() {
  echo -e "${CYAN}======================================${NC}"
  echo -e "${CYAN}       Cursor 工具集一键执行脚本       ${NC}"
  echo -e "${CYAN}======================================${NC}"
  echo -e "${YELLOW}请选择要执行的操作:${NC}"
  echo -e "${BLUE}1. 重置设备 ID (解决试用限制)${NC}"
  echo -e "${BLUE}2. 禁用自动更新 (锁定版本)${NC}"
  echo -e "${BLUE}3. 恢复自动更新${NC}"
  echo -e "${BLUE}0. 退出${NC}"
  echo -e "${CYAN}======================================${NC}"
  echo -ne "${YELLOW}请输入选项 [0-3]: ${NC}"
}

# 执行工具集命令
run_tool() {
  local platform=$(detect_platform)
  local executable=$(get_executable_path "$platform")
  local command=$1

  echo -e "${BLUE}执行: $2${NC}"

  if [ -f "$executable" ]; then
    if [ -n "$command" ]; then
      "$executable" "$command"
    else
      "$executable"
    fi
  else
    echo -e "${YELLOW}⚠️ 可执行文件不存在，尝试下载...${NC}"
    if download_executable "$platform"; then
      if [ -n "$command" ]; then
        "$executable" "$command"
      else
        "$executable"
      fi
    else
      echo -e "${RED}❌ 无法获取工具集${NC}"
      return 1
    fi
  fi
}

# 清理临时文件
cleanup() {
  # 保留下载的可执行文件，以便下次使用
  # 如果需要完全清理，取消下面的注释
  # rm -rf "$TMP_DIR"
  :
}

# 检查更新
check_update() {
  echo -e "${BLUE}检查更新...${NC}"

  # 获取最新版本
  local latest_version
  if command -v curl >/dev/null 2>&1; then
    latest_version=$(curl -s "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/releases/latest" | grep -o '"tag_name": "v[^"]*"' | cut -d'"' -f4 | cut -c2-)
  elif command -v wget >/dev/null 2>&1; then
    latest_version=$(wget -q -O - "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/releases/latest" | grep -o '"tag_name": "v[^"]*"' | cut -d'"' -f4 | cut -c2-)
  else
    echo -e "${YELLOW}⚠️ 无法检查更新 (需要 curl 或 wget)${NC}"
    return
  fi

  if [ -z "$latest_version" ]; then
    echo -e "${YELLOW}⚠️ 无法获取最新版本信息${NC}"
    return
  fi

  # 比较版本
  if [ "$latest_version" != "$VERSION" ]; then
    echo -e "${YELLOW}⚠️ 发现新版本: $latest_version (当前版本: $VERSION)${NC}"
    echo -e "${YELLOW}⚠️ 请访问 https://github.com/$REPO_OWNER/$REPO_NAME/releases/latest 获取最新版本${NC}"
  else
    echo -e "${GREEN}✅ 当前已是最新版本${NC}"
  fi
}

# 主函数
main() {
  # 检查更新
  check_update

  # 显示菜单并获取用户选择
  show_menu
  read choice

  # 根据用户选择执行相应操作
  case $choice in
    1)
      run_tool "reset" "重置设备 ID"
      ;;
    2)
      run_tool "disable-update" "禁用自动更新"
      ;;
    3)
      run_tool "enable-update" "恢复自动更新"
      ;;
    0)
      echo -e "${GREEN}感谢使用，再见！${NC}"
      ;;
    *)
      echo -e "${RED}❌ 无效的选项${NC}"
      ;;
  esac

  # 清理临时文件
  cleanup
}

# 执行主函数
main