#!/usr/bin/env python3
"""
简单的版本更新工具

用法:
    python update_version.py <新版本号>

示例:
    python update_version.py 1.0.1
"""

import sys
import json
import re
from pathlib import Path

def update_version_config(new_version):
    """更新 version_config.json 文件中的版本号"""
    config_path = Path("version_config.json")

    if not config_path.exists():
        print("错误: version_config.json 文件不存在")
        return False

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        old_version = config['VERSION']
        config['VERSION'] = new_version

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        print(f"✅ 已更新 version_config.json 中的版本号: {old_version} -> {new_version}")
        return True
    except Exception as e:
        print(f"❌ 更新 version_config.json 失败: {e}")
        return False

def update_version_in_code(new_version):
    """更新 cursor_tools.py 中的版本号"""
    cursor_tools_path = Path("cursor_tools.py")

    if not cursor_tools_path.exists():
        print("错误: cursor_tools.py 文件不存在")
        return False

    try:
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
    except Exception as e:
        print(f"❌ 更新 cursor_tools.py 失败: {e}")
        return False

def update_poetry_version(new_version):
    """更新 pyproject.toml 中的版本号"""
    try:
        import subprocess
        result = subprocess.run(f"poetry version {new_version}", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ 已更新 Poetry 版本为 {new_version}")
            return True
        else:
            print(f"❌ 更新 Poetry 版本失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 更新 Poetry 版本失败: {e}")
        return False

def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    new_version = sys.argv[1]

    # 验证版本号格式
    if not re.match(r'^\d+\.\d+\.\d+$', new_version):
        print("❌ 无效的版本号格式，请使用 x.y.z 格式")
        sys.exit(1)

    # 更新各处的版本号
    config_updated = update_version_config(new_version)
    code_updated = update_version_in_code(new_version)
    poetry_updated = update_poetry_version(new_version)

    if config_updated and code_updated and poetry_updated:
        print("\n✅ 版本更新完成!")
        print("请记得手动更新 CHANGELOG.md 文件，添加新版本的变更记录")
        print("\n提交更改:")
        print(f"git add pyproject.toml cursor_tools.py version_config.json CHANGELOG.md")
        print(f'git commit -m "build: 版本更新至 v{new_version}"')
        print(f"git tag v{new_version}")
        print(f"git push && git push --tags")
    else:
        print("\n⚠️ 版本更新过程中出现问题，请检查上述错误信息")

if __name__ == "__main__":
    main()