#!/bin/bash
# Cursor 工具集一键执行脚本
# 支持 macOS, Linux 和 Windows (通过 Git Bash 或 WSL)

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
BRANCH="main"

# 脚本 URL
RESET_SCRIPT_URL="https://raw.githubusercontent.com/$REPO_OWNER/$REPO_NAME/$BRANCH/scripts/reset_cursor.sh"

# 临时文件路径
TMP_DIR="/tmp/cursor-tools"
RESET_SCRIPT_PATH="$TMP_DIR/reset_cursor.sh"

# 检测操作系统
detect_os() {
  case "$(uname -s)" in
    Darwin*)  echo "macos" ;;
    Linux*)
      if grep -q Microsoft /proc/version 2>/dev/null; then
        echo "wsl"
      else
        echo "linux"
      fi
      ;;
    MINGW*|MSYS*|CYGWIN*) echo "windows" ;;
    *) echo "unknown" ;;
  esac
}

# 下载脚本
download_scripts() {
  echo -e "${BLUE}正在下载脚本...${NC}"

  # 创建临时目录
  mkdir -p "$TMP_DIR"

  # 下载重置脚本
  if command -v curl >/dev/null 2>&1; then
    curl -s -o "$RESET_SCRIPT_PATH" "$RESET_SCRIPT_URL"
  elif command -v wget >/dev/null 2>&1; then
    wget -q -O "$RESET_SCRIPT_PATH" "$RESET_SCRIPT_URL"
  else
    echo -e "${RED}❌ 需要 curl 或 wget 来下载脚本${NC}"
    return 1
  fi

  # 设置执行权限
  chmod +x "$RESET_SCRIPT_PATH"

  if [ -f "$RESET_SCRIPT_PATH" ]; then
    echo -e "${GREEN}✅ 脚本下载成功${NC}"
    return 0
  else
    echo -e "${RED}❌ 脚本下载失败${NC}"
    return 1
  fi
}

# 显示菜单
show_menu() {
  echo -e "${CYAN}======================================${NC}"
  echo -e "${CYAN}       Cursor 工具集一键执行脚本       ${NC}"
  echo -e "${CYAN}======================================${NC}"
  echo -e "${YELLOW}请选择要执行的操作:${NC}"
  echo -e "${BLUE}1. 重置 Cursor 设备 ID (解决试用限制)${NC}"
  echo -e "${BLUE}0. 退出${NC}"
  echo -e "${CYAN}======================================${NC}"
  echo -ne "${YELLOW}请输入选项 [0-1]: ${NC}"
}

# 执行重置设备 ID
run_reset() {
  echo -e "${BLUE}执行: 重置 Cursor 设备 ID${NC}"
  bash "$RESET_SCRIPT_PATH"
}

# 清理临时文件
cleanup() {
  rm -rf "$TMP_DIR"
}

# 主函数
main() {
  # 下载脚本
  if ! download_scripts; then
    return 1
  fi

  # 显示菜单并获取用户选择
  show_menu
  read choice

  # 根据用户选择执行相应操作
  case $choice in
    1)
      run_reset
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