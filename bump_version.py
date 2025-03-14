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

def run_command(cmd):
    """运行命令并返回输出"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"错误: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()

def update_version_in_code(new_version):
    """更新 reset_cursor.py 中的版本号"""
    reset_cursor_path = Path("reset_cursor.py")
    if not reset_cursor_path.exists():
        print("错误: reset_cursor.py 文件不存在")
        return False

    content = reset_cursor_path.read_text(encoding="utf-8")
    # 查找并替换版本号
    pattern = r"v\d+\.\d+\.\d+"
    if re.search(pattern, content):
        new_content = re.sub(pattern, f"v{new_version}", content)
        reset_cursor_path.write_text(new_content, encoding="utf-8")
        print(f"✅ 已更新 reset_cursor.py 中的版本号为 v{new_version}")
        return True
    else:
        print("⚠️ 在 reset_cursor.py 中未找到版本号模式")
        return False

def update_changelog(version, message):
    """更新 CHANGELOG.md 文件"""
    changelog_path = Path("CHANGELOG.md")
    today = datetime.now().strftime("%Y-%m-%d")

    if not changelog_path.exists():
        # 如果文件不存在，创建一个新的
        content = f"# 更新日志\n\n## v{version} ({today})\n\n- {message}\n"
    else:
        # 如果文件存在，在顶部添加新的版本信息
        content = changelog_path.read_text(encoding="utf-8")
        new_entry = f"## v{version} ({today})\n\n- {message}\n\n"

        # 查找第一个版本标题的位置
        match = re.search(r"## v\d+\.\d+\.\d+", content)
        if match:
            # 在第一个版本标题前插入新版本
            pos = match.start()
            content = content[:pos] + new_entry + content[pos:]
        else:
            # 如果没有找到版本标题，可能是新文件或格式不同
            content += f"\n## v{version} ({today})\n\n- {message}\n"

    # 写入文件
    changelog_path.write_text(content, encoding="utf-8")
    print(f"✅ 已更新 CHANGELOG.md")
    return True

def main():
    parser = argparse.ArgumentParser(description="版本号更新工具")
    parser.add_argument("bump_type", choices=["major", "minor", "patch"], help="版本号更新类型")
    parser.add_argument("--message", "-m", required=True, help="版本更新说明")

    args = parser.parse_args()

    # 使用 Poetry 获取当前版本
    current_version = run_command("poetry version -s")
    print(f"当前版本: {current_version}")

    # 使用 Poetry 更新版本号
    new_version = run_command(f"poetry version {args.bump_type}")
    new_version = new_version.split()[-1]  # 提取版本号
    print(f"新版本: {new_version}")

    # 更新代码中的版本号
    update_version_in_code(new_version)

    # 更新更新日志
    update_changelog(new_version, args.message)

    # 提示用户提交更改
    print("\n✅ 版本更新完成!")
    print(f"请检查更改并提交 Git:")
    print(f"git add pyproject.toml reset_cursor.py CHANGELOG.md")
    print(f'git commit -m "build: 版本更新至 v{new_version}"')
    print(f"git tag v{new_version}")
    print(f"git push && git push --tags")

if __name__ == "__main__":
    main()