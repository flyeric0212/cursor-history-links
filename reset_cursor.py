#!/usr/bin/env python3
'''
Cursor 试用限制重置工具

此脚本用于重置 Cursor 配置文件中的设备 ID，生成新的随机设备 ID，
从而解决"You've reached your trial request limit"或
"Too many free trial accounts used on this machine"的问题。

适用于 Cursor v0.46 和 v0.47 版本
'''

import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
import platform

def backup_file(file_path: str):
    """创建指定文件的时间戳备份"""
    if os.path.exists(file_path):
        backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(file_path, backup_path)
        print(f"✅ 已创建备份文件: {backup_path}")

def get_storage_file():
    """根据操作系统确定存储文件位置"""
    system = platform.system()
    if system == "Windows":
        return Path(os.getenv("APPDATA")) / "Cursor" / "User" / "globalStorage" / "storage.json"
    elif system == "Darwin":  # macOS
        return Path(os.path.expanduser("~")) / "Library" / "Application Support" / "Cursor" / "User" / "globalStorage" / "storage.json"
    elif system == "Linux":
        return Path(os.path.expanduser("~")) / ".config" / "Cursor" / "User" / "globalStorage" / "storage.json"
    else:
        raise OSError(f"不支持的操作系统: {system}")

def reset_cursor_id():
    """重置 Cursor 的设备 ID"""
    storage_file = get_storage_file()

    # 确保父目录存在
    storage_file.parent.mkdir(parents=True, exist_ok=True)

    # 备份原始文件
    backup_file(storage_file)

    # 读取或创建配置数据
    if not storage_file.exists():
        data = {}
        print("⚠️ 未找到配置文件，将创建新的配置文件")
    else:
        try:
            with open(storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print("✅ 成功读取配置文件")
        except json.JSONDecodeError:
            print("⚠️ 配置文件格式错误，将创建新的配置数据")
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
    try:
        with open(storage_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print("🎉 设备 ID 已成功重置。新的设备 ID 为: \n")
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
    except Exception as e:
        print(f"❌ 写入配置文件时出错: {e}")

def main():
    print("🔄 Cursor 试用限制重置工具")
    print("⚠️ 请确保已完全关闭 Cursor 应用程序后再继续")

    try:
        input("按回车键继续...")
        reset_cursor_id()
        print("\n✅ 重置完成！请重新启动 Cursor 应用程序")
        print("⚠️ 注意：如果 Cursor 仍在后台运行，重置可能不会成功")
    except KeyboardInterrupt:
        print("\n❌ 操作已取消")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")

if __name__ == "__main__":
    main()