#!/usr/bin/env python3
"""
版本号更新工具

用法:
    python scripts/bump_version.py [major|minor|patch] [--message "更新说明"]

示例:
    python scripts/bump_version.py patch --message "修复了某个问题"
    python scripts/bump_version.py minor --message "添加了新功能"
    python scripts/bump_version.py major --message "重大更新"
"""

import os
import sys
import re
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

def run_command(cmd):
    """运行命令并返回输出"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"错误: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()

def read_env_file() -> Dict[str, str]:
    """读取 .env 文件中的环境变量"""
    env_vars = {}
    env_path = Path(".env")

    if env_path.exists():
        content = env_path.read_text(encoding="utf-8")
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()

    return env_vars

def write_env_file(env_vars: Dict[str, str]):
    """将环境变量写入 .env 文件"""
    env_path = Path(".env")
    content = "\n".join([f"{key}={value}" for key, value in env_vars.items()])
    env_path.write_text(content, encoding="utf-8")
    print(f"✅ 已更新 .env 文件")

def update_version_in_code(new_version: str) -> bool:
    """更新 cursor_tools.py 中的版本号"""
    cursor_tools_path = Path("cursor_tools.py")
    if not cursor_tools_path.exists():
        print("错误: cursor_tools.py 文件不存在")
        return False

    content = cursor_tools_path.read_text(encoding="utf-8")
    # 查找并替换版本号
    pattern = r"v\d+\.\d+\.\d+"
    if re.search(pattern, content):
        new_content = re.sub(pattern, f"v{new_version}", content)
        cursor_tools_path.write_text(new_content, encoding="utf-8")
        print(f"✅ 已更新 cursor_tools.py 中的版本号为 v{new_version}")
        return True
    else:
        print("⚠️ 在 cursor_tools.py 中未找到版本号模式")
        return False

def update_changelog(version: str, messages: List[str]) -> bool:
    """更新 CHANGELOG.md 文件，使用新的格式"""
    changelog_path = Path("CHANGELOG.md")

    if not changelog_path.exists():
        # 如果文件不存在，创建一个新的
        content = f"# Change Log\n\n## v{version}\n"
        for i, msg in enumerate(messages, 1):
            content += f"{i}. {msg}\n"
    else:
        # 如果文件存在，在顶部添加新的版本信息
        content = changelog_path.read_text(encoding="utf-8")

        # 确保文件有标题
        if not content.startswith("# Change Log"):
            content = "# Change Log\n\n" + content

        # 创建新版本的条目
        new_entry = f"## v{version}\n"
        for i, msg in enumerate(messages, 1):
            new_entry += f"{i}. {msg}\n"
        new_entry += "\n"

        # 查找第一个版本标题的位置
        match = re.search(r"## v\d+\.\d+\.\d+", content)
        if match:
            # 在第一个版本标题前插入新版本
            pos = match.start()
            content = content[:pos] + new_entry + content[pos:]
        else:
            # 如果没有找到版本标题，添加到文件末尾
            content += f"\n{new_entry}"

    # 写入文件
    changelog_path.write_text(content, encoding="utf-8")
    print(f"✅ 已更新 CHANGELOG.md")
    return True

def bump_version(current_version: str, bump_type: str) -> str:
    """根据指定的类型增加版本号"""
    major, minor, patch = map(int, current_version.split('.'))

    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"未知的版本更新类型: {bump_type}")

def main():
    parser = argparse.ArgumentParser(description="版本号更新工具")
    parser.add_argument("bump_type", choices=["major", "minor", "patch"], help="版本号更新类型")
    parser.add_argument("--message", "-m", required=True, help="版本更新说明，多个说明用逗号分隔")

    args = parser.parse_args()

    # 获取当前版本号
    env_vars = read_env_file()
    if "VERSION" in env_vars:
        current_version = env_vars["VERSION"]
        print(f"当前版本 (从 .env): {current_version}")
    else:
        # 如果 .env 文件中没有版本号，则从 Poetry 获取
        current_version = run_command("poetry version -s")
        print(f"当前版本 (从 Poetry): {current_version}")
        env_vars["VERSION"] = current_version
        env_vars.setdefault("APP_NAME", "Cursor 工具集")
        env_vars.setdefault("AUTHOR", "Eric")
        env_vars.setdefault("EMAIL", "bo.liang0212@outlook.com")

    # 计算新版本号
    new_version = bump_version(current_version, args.bump_type)
    print(f"新版本: {new_version}")

    # 更新 .env 文件
    env_vars["VERSION"] = new_version
    write_env_file(env_vars)

    # 使用 Poetry 更新版本号
    run_command(f"poetry version {new_version}")
    print(f"✅ 已更新 Poetry 版本为 {new_version}")

    # 更新代码中的版本号
    update_version_in_code(new_version)

    # 处理更新说明，支持多条
    messages = [msg.strip() for msg in args.message.split(",")]

    # 更新更新日志
    update_changelog(new_version, messages)

    # 提示用户提交更改
    print("\n✅ 版本更新完成!")
    print(f"请检查更改并提交 Git:")
    print(f"git add pyproject.toml cursor_tools.py CHANGELOG.md .env")
    print(f'git commit -m "build: 版本更新至 v{new_version}"')
    print(f"git tag v{new_version}")
    print(f"git push && git push --tags")

if __name__ == "__main__":
    main()