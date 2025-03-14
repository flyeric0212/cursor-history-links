#!/bin/bash
# Cursor 试用限制重置工具 - Bash 版本
# 支持 macOS, Linux 和 Windows (通过 Git Bash 或 WSL)

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

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

# 获取存储文件路径
get_storage_path() {
  local os=$1
  local home_dir="$HOME"

  case "$os" in
    macos)
      echo "$home_dir/Library/Application Support/Cursor/User/globalStorage/storage.json"
      ;;
    linux|wsl)
      echo "$home_dir/.config/Cursor/User/globalStorage/storage.json"
      ;;
    windows)
      # 在 Git Bash 中，APPDATA 环境变量可能不存在，尝试使用 Windows 路径
      if [ -n "$APPDATA" ]; then
        # 将 Windows 路径转换为 Git Bash 路径
        echo "$(echo $APPDATA | sed 's/\\/\//g')/Cursor/User/globalStorage/storage.json"
      else
        echo "$home_dir/AppData/Roaming/Cursor/User/globalStorage/storage.json"
      fi
      ;;
    *)
      echo ""
      ;;
  esac
}

# 生成随机 ID
generate_random_id() {
  # 生成 32 字节的随机十六进制字符串
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 32
  else
    # 备用方法，生成 64 个随机十六进制字符
    cat /dev/urandom 2>/dev/null | tr -dc 'a-f0-9' | head -c 64 ||
    date +%s | sha256sum | head -c 64 ||
    date | md5sum | head -c 64
  fi
}

# 生成 UUID
generate_uuid() {
  # 尝试使用系统 UUID 生成工具
  if command -v uuidgen >/dev/null 2>&1; then
    uuidgen | tr -d '\n'
    return
  fi

  # 备用方法：手动生成 UUID v4
  local hex=$(cat /dev/urandom 2>/dev/null | tr -dc 'a-f0-9' | head -c 32 ||
              date +%s | sha256sum | head -c 32 ||
              date | md5sum | head -c 32)

  echo "${hex:0:8}-${hex:8:4}-4${hex:13:3}-${hex:16:4}-${hex:20:12}"
}

# 备份文件
backup_file() {
  local file_path=$1
  if [ -f "$file_path" ]; then
    local backup_path="${file_path}.backup_$(date +%Y%m%d_%H%M%S)"
    cp "$file_path" "$backup_path"
    echo -e "${GREEN}✅ 已创建备份文件: $backup_path${NC}"
    return 0
  fi
  return 1
}

# 重置 Cursor ID
reset_cursor_id() {
  local os=$(detect_os)
  local storage_file=$(get_storage_path "$os")

  if [ -z "$storage_file" ]; then
    echo -e "${RED}❌ 不支持的操作系统${NC}"
    return 1
  fi

  # 确保父目录存在
  mkdir -p "$(dirname "$storage_file")"

  # 备份原始文件
  backup_file "$storage_file"

  # 读取或创建配置数据
  local data="{}"
  if [ -f "$storage_file" ]; then
    if [ -s "$storage_file" ]; then
      data=$(cat "$storage_file")
      echo -e "${GREEN}✅ 成功读取配置文件${NC}"
    else
      echo -e "${YELLOW}⚠️ 配置文件为空，将创建新的配置数据${NC}"
    fi
  else
    echo -e "${YELLOW}⚠️ 未找到配置文件，将创建新的配置文件${NC}"
  fi

  # 生成新的随机 ID
  local machine_id=$(generate_random_id)
  local mac_machine_id=$(generate_random_id)
  local dev_device_id=$(generate_uuid)
  local sqm_id=$(generate_uuid)

  # 创建新的 JSON 数据
  # 注意：这是一个简单的方法，不处理复杂的 JSON 结构
  # 对于生产环境，建议使用 jq 等工具处理 JSON
  if command -v jq >/dev/null 2>&1; then
    # 使用 jq 处理 JSON
    echo "$data" | jq --arg mid "$machine_id" \
                      --arg mmid "$mac_machine_id" \
                      --arg did "$dev_device_id" \
                      --arg sid "$sqm_id" \
                      '.["telemetry.machineId"]=$mid |
                       .["telemetry.macMachineId"]=$mmid |
                       .["telemetry.devDeviceId"]=$did |
                       .["telemetry.sqmId"]=$sid' > "$storage_file"
  else
    # 备用方法：创建新的 JSON 文件
    cat > "$storage_file" << EOF
{
  "telemetry.machineId": "$machine_id",
  "telemetry.macMachineId": "$mac_machine_id",
  "telemetry.devDeviceId": "$dev_device_id",
  "telemetry.sqmId": "$sqm_id"
}
EOF
  fi

  if [ $? -eq 0 ]; then
    echo -e "${GREEN}🎉 设备 ID 已成功重置。新的设备 ID 为:${NC}"
    echo ""
    echo "{
  \"machineId\": \"$machine_id\",
  \"macMachineId\": \"$mac_machine_id\",
  \"devDeviceId\": \"$dev_device_id\",
  \"sqmId\": \"$sqm_id\"
}"
    return 0
  else
    echo -e "${RED}❌ 写入配置文件时出错${NC}"
    return 1
  fi
}

# 主函数
main() {
  echo -e "${BLUE}🔄 Cursor 试用限制重置工具 - Bash 版本${NC}"
  echo -e "${YELLOW}⚠️ 请确保已完全关闭 Cursor 应用程序后再继续${NC}"

  read -p "按回车键继续..."

  reset_cursor_id

  if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ 重置完成！请重新启动 Cursor 应用程序${NC}"
    echo -e "${YELLOW}⚠️ 注意：如果 Cursor 仍在后台运行，重置可能不会成功${NC}"
  fi
}

# 如果直接运行此脚本（而不是作为库导入），则执行主函数
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  main
fi