#!/usr/bin/env python3
'''
Cursor 工具集

此脚本整合了多种 Cursor 编辑器实用工具，包括：
1. 重置设备 ID - 解决试用限制问题
2. 禁用自动更新 - 锁定 Cursor 版本

适用于 Cursor v0.46 和 v0.47 版本
'''

import os
import sys
import json
import platform
import shutil
import subprocess
import time
import uuid
import re
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Literal, Union, Callable, List, Tuple, Any

# 定义操作系统类型
OSType = Literal["Windows", "Darwin", "Linux"]

# 定义颜色代码（如果在支持颜色的终端中）
if sys.platform != "win32" or "ANSICON" in os.environ:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    RESET = "\033[0m"
else:
    GREEN = YELLOW = RED = BLUE = BOLD = RESET = ""

# 定义表情符号
EMOJI = {
    "INFO": "ℹ️ ",
    "SUCCESS": "✅ ",
    "ERROR": "❌ ",
    "WARNING": "⚠️ ",
    "PROCESS": "🔄 ",
    "LOCK": "🔒 ",
    "FOLDER": "📁 ",
    "FILE": "📄 ",
    "STATS": "📊 ",
    "RESET": "🔄 "
}

# 定义文件路径映射
CURSOR_PATHS: Dict[OSType, Dict[str, Callable[[], Path]]] = {
    "Windows": {
        "storage": lambda: Path(os.path.join(os.getenv("APPDATA", ""), "Cursor", "User", "globalStorage", "storage.json")),
        "version": lambda: Path(os.path.join(os.getenv("APPDATA", ""), "Cursor", "product.json")),
        "updater": lambda: Path(os.path.join(os.getenv("LOCALAPPDATA", ""), "cursor-updater"))
    },
    "Darwin": {  # macOS
        "storage": lambda: Path(os.path.join(str(Path.home()), "Library", "Application Support", "Cursor", "User", "globalStorage", "storage.json")),
        "version": lambda: Path(os.path.join("/Applications", "Cursor.app", "Contents", "Resources", "app", "product.json")),
        "updater": lambda: Path(os.path.join(str(Path.home()), "Library", "Application Support", "cursor-updater"))
    },
    "Linux": {
        "storage": lambda: Path(os.path.join(str(Path.home()), ".config", "Cursor", "User", "globalStorage", "storage.json")),
        "version": lambda: Path(os.path.join("/usr/share", "cursor", "resources", "app", "product.json")),
        "updater": lambda: Path(os.path.join(str(Path.home()), ".config", "cursor-updater"))
    }
}

# 通用工具函数
def print_header(title: str) -> None:
    """打印脚本标题"""
    print(f"\n{BLUE}{BOLD}{'='*60}{RESET}")
    print(f"{BLUE}{BOLD}{title}{RESET}")
    print(f"{BLUE}{BOLD}{'='*60}{RESET}\n")

def print_step(emoji: str, message: str) -> None:
    """打印步骤信息"""
    print(f"{BLUE}{emoji} {message}...{RESET}")

def print_success(message: str) -> None:
    """打印成功信息"""
    print(f"{GREEN}{EMOJI['SUCCESS']}{message}{RESET}")

def print_error(message: str) -> None:
    """打印错误信息"""
    print(f"{RED}{EMOJI['ERROR']}{message}{RESET}")

def print_warning(message: str) -> None:
    """打印警告信息"""
    print(f"{YELLOW}{EMOJI['WARNING']}{message}{RESET}")

def get_system() -> OSType:
    """获取当前操作系统类型

    Returns:
        当前操作系统类型

    Raises:
        OSError: 如果操作系统不受支持
    """
    system = platform.system()
    if system not in ("Windows", "Darwin", "Linux"):
        raise OSError(f"不支持的操作系统: {system}")
    return system  # type: ignore

def get_cursor_path(path_type: str) -> Path:
    """获取Cursor相关文件路径

    Args:
        path_type: 路径类型，可选值: "storage", "version", "updater"

    Returns:
        对应的文件路径

    Raises:
        ValueError: 如果路径类型不支持
        OSError: 如果操作系统不受支持
    """
    system = get_system()

    try:
        return CURSOR_PATHS[system][path_type]()
    except KeyError:
        raise ValueError(f"不支持的路径类型: {path_type}")

def backup_file(file_path: Union[str, Path]) -> bool:
    """创建文件备份

    Args:
        file_path: 需要备份的文件路径

    Returns:
        备份是否成功
    """
    file_path = Path(file_path)
    if file_path.exists():
        backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            if file_path.is_dir():
                shutil.copytree(file_path, backup_path)
            else:
                shutil.copy2(file_path, backup_path)
            print_success(f"已创建备份: {backup_path}")
            return True
        except Exception as e:
            print_error(f"创建备份失败: {e}")
    return False

def is_cursor_running() -> bool:
    """检测 Cursor 是否正在运行

    Returns:
        如果Cursor正在运行返回True，否则返回False
    """
    system = get_system()
    try:
        if system == "Windows":
            output = subprocess.check_output("tasklist", shell=True, text=True)
            return "Cursor.exe" in output
        elif system in ("Darwin", "Linux"):  # macOS和Linux使用相同的命令
            output = subprocess.check_output(
                "ps -A | grep -i cursor",
                shell=True,
                text=True,
                stderr=subprocess.DEVNULL
            )
            return bool(output.strip()) and "grep" not in output
        return False
    except subprocess.CalledProcessError:
        return False

def kill_cursor_processes() -> bool:
    """结束所有Cursor进程

    Returns:
        是否成功结束所有进程
    """
    try:
        print_step(EMOJI["PROCESS"], "正在结束 Cursor 进程")
        system = get_system()

        if system == "Windows":
            subprocess.run(['taskkill', '/F', '/IM', 'Cursor.exe', '/T'],
                          capture_output=True)
        elif system in ("Darwin", "Linux"):  # macOS和Linux使用相同的命令
            subprocess.run(['pkill', '-f', 'Cursor'],
                          capture_output=True)

        # 等待进程完全结束
        time.sleep(1)

        if is_cursor_running():
            print_warning("部分Cursor进程可能仍在运行")
            return False
        else:
            print_success("Cursor 进程已结束")
            return True
    except Exception as e:
        print_error(f"结束进程失败: {e}")
        return False

def check_cursor_status() -> bool:
    """检查Cursor状态并处理运行中的进程

    Returns:
        是否可以继续操作（True表示可以继续）
    """
    if is_cursor_running():
        print_warning("检测到Cursor正在运行")
        choice = input("是否结束Cursor进程? (y/n): ").lower()
        if choice == 'y':
            if not kill_cursor_processes():
                print_warning("无法完全结束Cursor进程，继续操作可能会失败")
                choice = input("是否继续? (y/n): ").lower()
                if choice != 'y':
                    print_warning("操作已取消")
                    return False
        else:
            print_warning("操作已取消")
            return False
    return True

def get_cursor_version() -> str:
    """获取已安装的 Cursor 版本

    Returns:
        Cursor版本号，如果无法获取则返回"未知"
    """
    try:
        # 尝试从版本文件获取
        version_file = get_cursor_path("version")
        if version_file.exists():
            try:
                with open(version_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("version", "未知")
            except (json.JSONDecodeError, FileNotFoundError):
                pass

        # 如果无法从文件获取版本，尝试从 storage.json 中推断
        storage_file = get_cursor_path("storage")
        if storage_file.exists():
            with open(storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 从配置数据中尝试推断版本
                for key in data.keys():
                    if "version" in key.lower() and isinstance(data[key], str):
                        version_match = re.search(r'(\d+\.\d+(\.\d+)?)', data[key])
                        if version_match:
                            return version_match.group(1)
    except (OSError, ValueError, Exception) as e:
        print_warning(f"获取版本信息时出错: {e}")

    return "未知"

def check_version_compatibility() -> bool:
    """检查Cursor版本兼容性

    Returns:
        是否兼容（True表示兼容）
    """
    cursor_version = get_cursor_version()
    print_step(EMOJI["STATS"], f"检测到 Cursor 版本: {cursor_version}")

    if cursor_version != "未知":
        version_parts = cursor_version.split(".")
        if len(version_parts) >= 2:
            major, minor = int(version_parts[0]), int(version_parts[1])
            if major == 0 and (minor < 46 or minor > 47):
                print_warning(f"此工具主要适用于 Cursor v0.46 和 v0.47 版本，当前版本为 {cursor_version}")
                if input("是否继续? (y/n): ").lower() != 'y':
                    print_warning("操作已取消")
                    return False
    return True

# 功能1: 重置设备ID
def reset_cursor_id() -> bool:
    """重置 Cursor 的设备 ID

    Returns:
        是否成功重置
    """
    try:
        print_step(EMOJI["RESET"], "开始重置设备ID")
        storage_file = get_cursor_path("storage")

        # 确保父目录存在
        storage_file.parent.mkdir(parents=True, exist_ok=True)

        # 备份原始文件
        backup_file(storage_file)

        # 读取或创建配置数据
        if not storage_file.exists():
            data = {}
            print_warning("未找到配置文件，将创建新的配置文件")
        else:
            try:
                with open(storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print_success("成功读取配置文件")
            except json.JSONDecodeError:
                print_warning("配置文件格式错误，将创建新的配置数据")
                data = {}

        # 生成新的随机 ID
        machine_id = os.urandom(32).hex()
        mac_machine_id = os.urandom(32).hex()
        dev_device_id = str(uuid.uuid4())
        sqm_id = str(uuid.uuid4())

        # 更新配置数据
        data["telemetry.machineId"] = machine_id
        data["telemetry.macMachineId"] = mac_machine_id
        data["telemetry.devDeviceId"] = dev_device_id
        data["telemetry.sqmId"] = sqm_id

        # 写入更新后的配置
        with open(storage_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        print_success("设备 ID 已成功重置。新的设备 ID 为: \n")
        print(
            json.dumps(
                {
                    "machineId": machine_id,
                    "macMachineId": mac_machine_id,
                    "devDeviceId": dev_device_id,
                    "sqmId": sqm_id
                },
                indent=2,
                ensure_ascii=False
            )
        )
        return True
    except Exception as e:
        print_error(f"重置设备ID失败: {e}")
        return False

# 功能2: 禁用自动更新
def disable_auto_update() -> bool:
    """禁用Cursor自动更新

    Returns:
        是否成功禁用
    """
    try:
        print_step(EMOJI["LOCK"], "开始禁用自动更新")
        updater_path = get_cursor_path("updater")

        # 备份并删除更新程序目录
        print_step(EMOJI["FOLDER"], f"正在处理更新程序目录: {updater_path}")
        if os.path.exists(updater_path):
            if os.path.isdir(updater_path):
                backup_file(updater_path)
                shutil.rmtree(updater_path)
                print_success("更新程序目录已删除")
            else:
                # 如果已经是文件，检查是否为只读
                if not os.access(updater_path, os.W_OK):
                    print_success("更新程序已被禁用（文件已存在且为只读）")
                    return True
                else:
                    backup_file(updater_path)
                    os.remove(updater_path)
                    print_success("更新程序文件已删除")

        # 创建阻止文件
        print_step(EMOJI["FILE"], "正在创建阻止文件")

        # 确保父目录存在
        parent_dir = os.path.dirname(updater_path)
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)

        # 创建空文件
        with open(updater_path, 'w') as f:
            f.write("# 此文件由Cursor工具集创建\n")
            f.write("# 创建时间: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n")
            f.write("# 请勿删除此文件，否则Cursor将恢复自动更新\n")

        # 设置为只读
        system = get_system()
        if system == "Windows":
            os.system(f'attrib +r "{updater_path}"')
        else:
            os.chmod(updater_path, 0o444)  # 设置为只读 (r--r--r--)

        # 验证文件是否为只读
        if not os.access(updater_path, os.W_OK):
            print_success("阻止文件已创建并设置为只读")
        else:
            print_warning("无法将文件设置为只读，自动更新可能仍会生效")
            return False

        print_success("Cursor 自动更新已成功禁用")
        return True
    except Exception as e:
        print_error(f"禁用自动更新失败: {e}")
        return False

# 功能3: 恢复自动更新
def enable_auto_update() -> bool:
    """恢复Cursor自动更新功能

    Returns:
        是否成功恢复
    """
    try:
        print_step(EMOJI["INFO"], "开始恢复自动更新功能")
        updater_path = get_cursor_path("updater")

        # 删除阻止文件
        if os.path.exists(updater_path):
            # 如果是文件，尝试删除
            if not os.path.isdir(updater_path):
                # 在Windows上，需要先移除只读属性
                system = get_system()
                if system == "Windows":
                    os.system(f'attrib -r "{updater_path}"')
                else:
                    os.chmod(updater_path, 0o666)  # 设置为可写

                os.remove(updater_path)
                print_success("阻止文件已删除，自动更新功能已恢复")
                return True
            else:
                print_warning(f"{updater_path} 是一个目录，不需要删除")
                return True
        else:
            print_warning(f"{updater_path} 不存在，自动更新应该已经可用")
            return True
    except Exception as e:
        print_error(f"恢复自动更新失败: {e}")
        return False

# 命令行参数解析
def parse_arguments() -> argparse.Namespace:
    """解析命令行参数

    Returns:
        解析后的参数命名空间
    """
    parser = argparse.ArgumentParser(description="Cursor 工具集")

    # 创建子命令解析器
    subparsers = parser.add_subparsers(dest="command", help="要执行的命令")

    # 重置设备ID命令
    reset_parser = subparsers.add_parser("reset", help="重置设备ID，解决试用限制")
    reset_parser.add_argument("--force", "-f", action="store_true", help="跳过确认和检查，强制重置")

    # 禁用自动更新命令
    disable_parser = subparsers.add_parser("disable-update", help="禁用自动更新")
    disable_parser.add_argument("--force", "-f", action="store_true", help="跳过确认和检查，强制执行")

    # 恢复自动更新命令
    enable_parser = subparsers.add_parser("enable-update", help="恢复自动更新")
    enable_parser.add_argument("--force", "-f", action="store_true", help="跳过确认和检查，强制执行")

    # 版本信息
    parser.add_argument("--version", "-v", action="store_true", help="显示版本信息")

    return parser.parse_args()

# 主菜单
def show_main_menu() -> str:
    """显示主菜单并获取用户选择

    Returns:
        用户选择的选项
    """
    print(f"{BOLD}此工具集包含多种 Cursor 编辑器实用功能。{RESET}")
    print(f"{BOLD}适用于 Cursor v0.46 和 v0.47 版本。{RESET}\n")

    print("请选择操作:")
    print(f"{BLUE}1. 重置设备 ID (解决试用限制){RESET}")
    print(f"{BLUE}2. 禁用自动更新 (锁定版本){RESET}")
    print(f"{BLUE}3. 恢复自动更新{RESET}")
    print(f"{BLUE}0. 退出{RESET}")

    return input("\n请输入选项 [0-3]: ")

# 主函数
def main() -> None:
    """主函数"""
    args = parse_arguments()

    # 显示版本信息
    if args.version:
        print("Cursor 工具集 v1.0.0")
        sys.exit(0)

    # 如果指定了命令行命令，执行相应功能
    if args.command:
        if args.command == "reset":
            if args.force or (check_cursor_status() and check_version_compatibility()):
                reset_cursor_id()
        elif args.command == "disable-update":
            if args.force or check_cursor_status():
                disable_auto_update()
        elif args.command == "enable-update":
            if args.force or check_cursor_status():
                enable_auto_update()
    else:
        # 显示交互式菜单
        print_header(f"{EMOJI['LOCK']}  Cursor 工具集  {EMOJI['LOCK']}")

        choice = show_main_menu()

        if choice == "1":
            if check_cursor_status() and check_version_compatibility():
                reset_cursor_id()
        elif choice == "2":
            if check_cursor_status():
                disable_auto_update()
        elif choice == "3":
            if check_cursor_status():
                enable_auto_update()
        elif choice == "0":
            print_warning("操作已取消")
        else:
            print_error("无效的选项")

    print(f"\n{BLUE}{BOLD}{'='*60}{RESET}")
    input("按回车键退出...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n操作已取消")
    except Exception as e:
        print_error(f"发生错误: {e}")