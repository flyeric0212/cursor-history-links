import os
import json
import re
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, TypedDict
import httpx
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("cursor_updater")

# 获取东八区时间（UTC+8）
def get_utc8_time() -> datetime:
    """返回东八区（UTC+8）的当前时间"""
    return datetime.utcnow() + timedelta(hours=8)

# 类型定义
class PlatformInfo(TypedDict):
    platforms: List[str]
    readableNames: List[str]
    section: str

class VersionInfo(TypedDict):
    url: str
    version: str

class VersionHistoryEntry(TypedDict):
    version: str
    date: str
    platforms: Dict[str, str]  # platform -> download URL

class VersionHistory(TypedDict):
    versions: List[VersionHistoryEntry]

# 平台信息配置
PLATFORMS: Dict[str, PlatformInfo] = {
    "windows": {
        "platforms": ["win32-x64", "win32-arm64"],
        "readableNames": ["win32-x64", "win32-arm64"],
        "section": "Windows Installer"
    },
    "mac": {
        "platforms": ["darwin-universal", "darwin-x64", "darwin-arm64"],
        "readableNames": ["darwin-universal", "darwin-x64", "darwin-arm64"],
        "section": "Mac Installer"
    },
    "linux": {
        "platforms": ["linux-x64", "linux-arm64"],
        "readableNames": ["linux-x64", "linux-arm64"],
        "section": "Linux Installer"
    }
}

# 从URL或文件名中提取版本号
def extract_version(url: str) -> str:
    """
    从下载URL中提取Cursor版本号

    Args:
        url: 下载链接URL

    Returns:
        提取的版本号，如果无法提取则返回'Unknown'
    """
    # 对于Windows
    win_match = re.search(r'CursorUserSetup-[^-]+-([0-9.]+)\.exe', url)
    if win_match and win_match.group(1):
        return win_match.group(1)

    # 对于其他URL，尝试查找版本模式
    version_match = re.search(r'[0-9]+\.[0-9]+\.[0-9]+', url)
    return version_match.group(0) if version_match else 'Unknown'

# 格式化日期为YYYY-MM-DD
def format_date(date: datetime) -> str:
    """将日期对象格式化为YYYY-MM-DD格式的字符串"""
    return date.strftime('%Y-%m-%d')

# 获取平台的最新下载URL
async def fetch_latest_download_url(platform: str) -> Optional[str]:
    """
    从Cursor API获取指定平台的最新下载URL

    Args:
        platform: 平台标识符，如'darwin-universal'

    Returns:
        下载URL或None（如果请求失败）
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://www.cursor.com/api/download?platform={platform}&releaseTrack=latest",
                headers={
                    'User-Agent': 'Cursor-Version-Checker',
                    'Cache-Control': 'no-cache',
                }
            )

            if response.status_code != 200:
                raise Exception(f"HTTP error! status: {response.status_code}")

            data = response.json()
            return data.get("downloadUrl")
    except Exception as error:
        logger.error(f"获取平台 {platform} 的下载URL时出错: {error}")
        return None

# 从JSON文件读取版本历史
def read_version_history() -> VersionHistory:
    """
    读取version-history.json文件，如果不存在则返回空历史

    Returns:
        版本历史对象
    """
    history_path = Path.cwd() / "version-history.json"
    if history_path.exists():
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as error:
            logger.error(f'读取版本历史时出错: {error}')
            return {"versions": []}
    else:
        logger.warning('未找到version-history.json，将创建新文件')
        return {"versions": []}

# 保存版本历史到JSON文件
def save_version_history(history: VersionHistory) -> None:
    """
    将版本历史保存到version-history.json文件

    Args:
        history: 要保存的版本历史对象
    """
    if not history or not isinstance(history.get("versions"), list):
        logger.error('提供的版本历史对象无效')
        return

    history_path = Path.cwd() / "version-history.json"

    # 保留备份
    if history_path.exists():
        try:
            backup_path = Path(f"{history_path}.backup")
            history_path.replace(backup_path)
        except Exception as error:
            logger.warning(f'创建版本历史备份失败: {error}')

    try:
        json_data = json.dumps(history, indent=2)

        # 在写入文件前验证JSON有效性
        try:
            json.loads(json_data)
        except Exception as parse_error:
            logger.error(f'生成了无效的JSON数据，中止保存: {parse_error}')
            return

        # 先写入临时文件，然后重命名以避免部分写入
        temp_path = Path(f"{history_path}.tmp")
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(json_data)
        temp_path.replace(history_path)

        # 写入后验证文件是否存在
        if not history_path.exists():
            logger.error('保存版本历史失败：写入后文件不存在')
    except Exception as error:
        logger.error(f'保存版本历史时出错: {error}')
        raise  # 重新抛出以允许调用者处理

# 使用最新的Cursor链接更新README.md文件
async def update_readme(force_update=False) -> bool:
    """
    获取最新的Cursor下载链接并更新README.md文件

    Args:
        force_update: 是否强制更新，即使版本已存在

    Returns:
        更新是否成功
    """
    # 使用东八区时间
    current_time = get_utc8_time()
    logger.info(f"开始更新检查 - {current_time.isoformat()}")

    # 收集所有URL和版本
    results: Dict[str, Dict[str, VersionInfo]] = {}
    latest_version = '0.0.0'
    current_date = format_date(current_time)

    # 获取所有平台下载URL
    for os_key, os_data in PLATFORMS.items():
        results[os_key] = {}

        for platform in os_data["platforms"]:
            url = await fetch_latest_download_url(platform)

            if url:
                version = extract_version(url)
                results[os_key][platform] = {"url": url, "version": version}

                # 跟踪最高版本号
                if version != 'Unknown' and version > latest_version:
                    latest_version = version

    if latest_version == '0.0.0':
        logger.error('未能检索到任何有效的版本信息')
        return False

    logger.info(f"检测到最新版本: {latest_version}")

    # 使用version-history.json作为版本检查的唯一真实来源
    history = read_version_history()

    # 检查此版本是否已存在于版本历史中
    existing_version_index = next((i for i, entry in enumerate(history["versions"])
                                  if entry["version"] == latest_version), -1)

    # 如果版本已存在且不是强制更新，则退出
    if existing_version_index != -1 and not force_update:
        logger.info(f"版本 {latest_version} 已存在于版本历史中，无需更新")
        return False

    # 读取README
    readme_path = Path.cwd() / "README.md"
    if not readme_path.exists():
        logger.error('未找到README.md文件')
        return False

    with open(readme_path, 'r', encoding='utf-8') as f:
        readme_content = f.read()

    # 为历史条目创建新的平台对象
    platforms: Dict[str, str] = {}

    # 添加所有平台的URL
    for os_key in ['mac', 'windows', 'linux']:
        if os_key in results:
            for platform, info in results[os_key].items():
                platforms[platform] = info["url"]

    # 创建新条目
    new_entry: VersionHistoryEntry = {
        "version": latest_version,
        "date": current_date,
        "platforms": platforms
    }

    # 如果版本已存在，则更新现有条目，否则添加新条目
    if existing_version_index != -1:
        logger.info(f"更新版本历史中的版本 {latest_version}")
        history["versions"][existing_version_index] = new_entry
    else:
        logger.info(f"将新版本 {latest_version} 添加到version-history.json")
        history["versions"].append(new_entry)

    # 按版本排序（最新的在前）
    history["versions"].sort(key=lambda x: x["version"], reverse=True)

    # 删除重复的版本
    unique_versions = {}
    unique_history = []
    duplicates_count = 0
    for entry in history["versions"]:
        version = entry["version"]
        if version not in unique_versions:
            unique_versions[version] = True
            unique_history.append(entry)
        else:
            duplicates_count += 1

    if duplicates_count > 0:
        logger.info(f"删除了 {duplicates_count} 个重复版本")

    history["versions"] = unique_history

    # 将历史大小限制为100个条目，以防止无限增长
    if len(history["versions"]) > 100:
        history["versions"] = history["versions"][:100]
        logger.info("将版本历史截断为100个条目")

    # 重要：在更新README之前保存更新的历史JSON
    try:
        save_version_history(history)
    except Exception as error:
        logger.error(f'保存版本历史时出错: {error}')
        # 即使版本历史保存失败，也继续进行README更新

    # 生成平台链接
    def generate_platform_links(os_key, results):
        """生成指定操作系统的平台下载链接HTML"""
        links = []
        if os_key in results:
            for platform in PLATFORMS[os_key]["platforms"]:
                if platform in results[os_key] and results[os_key][platform]["url"]:
                    links.append(f"[{platform}]({results[os_key][platform]['url']})")
        return '<br>'.join(links) if links else ('Not Ready' if os_key == 'linux' else '')

    # 生成各平台链接
    mac_links = generate_platform_links('mac', results)
    windows_links = generate_platform_links('windows', results)
    linux_links = generate_platform_links('linux', results) or 'Not Ready'

    # 从version-history.json生成完整的表格
    table_rows = []

    # 遍历所有版本，生成表格行
    for entry in history["versions"]:
        version = entry["version"]
        date = entry["date"]
        platforms_data = entry["platforms"]

        # 生成各平台链接
        mac_urls = []
        win_urls = []
        linux_urls = []

        for os_key, platform_list in PLATFORMS.items():
            for platform in platform_list["platforms"]:
                if platform in platforms_data:
                    link = f"[{platform}]({platforms_data[platform]})"
                    if os_key == 'mac':
                        mac_urls.append(link)
                    elif os_key == 'windows':
                        win_urls.append(link)
                    elif os_key == 'linux':
                        linux_urls.append(link)

        mac_links = '<br>'.join(mac_urls) if mac_urls else ''
        windows_links = '<br>'.join(win_urls) if win_urls else ''
        linux_links = '<br>'.join(linux_urls) if linux_urls else 'Not Ready'

        # 生成表格行
        row = f"| {version} | {date} | {mac_links} | {windows_links} | {linux_links} |"
        table_rows.append(row)

    # 构建完整的表格
    table_header = "| Version | Date | Mac Installer | Windows Installer | Linux Installer |\n| --- | --- | --- | --- | --- |"
    table_content = table_header + "\n" + "\n".join(table_rows)

    # 替换README中的表格
    table_pattern = re.compile(r"\| Version \| Date \| Mac Installer \| Windows Installer \| Linux Installer \|\s*\n\|\s*---\s*\|\s*---\s*\|\s*---\s*\|\s*---\s*\|\s*---\s*\|(.*?)(?=\n\n|\Z)", re.DOTALL)
    readme_content = table_pattern.sub(table_content, readme_content)

    # 如果没有找到表格，则在文件末尾添加
    if not table_pattern.search(readme_content):
        readme_content += f"\n\n{table_content}\n"

    # 保存更新的README
    try:
        # 更新"脚本最后更新"时间，使用东八区时间
        current_time_str = get_utc8_time().strftime('%Y-%m-%d %H:%M:%S')
        readme_content = re.sub(r'脚本最后更新: `[^`]*`', f'脚本最后更新: `{current_time_str}`', readme_content)

        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        logger.info(f"README.md已更新为包含最新Cursor版本")
    except Exception as error:
        logger.error(f'保存README时出错: {error}')
        return False

    return True

# 主函数，以适当的错误处理运行更新
async def main() -> None:
    """主函数，运行更新过程并处理错误"""
    try:
        start_time = time.time()
        logger.info(f"开始更新过程")

        # 运行更新，强制更新README.md
        updated = await update_readme(force_update=True)
        elapsed_time = int((time.time() - start_time) * 1000)

        if updated:
            logger.info(f"更新成功完成，耗时 {elapsed_time}ms。找到新版本。")
        else:
            logger.info(f"更新完成，耗时 {elapsed_time}ms。未找到新版本。")

        # 在结束时验证文件完整性
        verify_file_integrity()
    except Exception as error:
        logger.critical(f'更新过程中出现严重错误: {error}', exc_info=True)
        # 如果进程以非零退出，任何GitHub Action都会将工作流标记为失败
        exit(1)

def verify_file_integrity():
    """验证version-history.json和README.md的完整性和一致性"""
    history_path = Path.cwd() / "version-history.json"
    readme_path = Path.cwd() / "README.md"

    if not history_path.exists():
        logger.warning('警告：更新后version-history.json不存在。这可能表明存在问题。')
        return

    try:
        # 验证JSON文件有效性
        with open(history_path, 'r', encoding='utf-8') as f:
            content = f.read()
            history_json = json.loads(content)

        if not readme_path.exists():
            logger.warning('README.md文件不存在，无法验证一致性。')
            return

        # 验证README和JSON的一致性
        with open(readme_path, 'r', encoding='utf-8') as f:
            readme_content = f.read()

        # 从表格中提取最新版本
        version_match = re.search(r'\| (\d+\.\d+\.\d+) \| (\d{4}-\d{2}-\d{2}) \|', readme_content)
        if not version_match:
            logger.warning('无法从README.md中提取版本信息。')
            return

        latest_version_in_readme = version_match.group(1)
        latest_date_in_readme = version_match.group(2)

        # 检查此版本是否存在于历史中
        version_exists = any(v["version"] == latest_version_in_readme for v in history_json["versions"])
        if not version_exists:
            logger.warning(f"警告：版本 {latest_version_in_readme} 在README.md中但不在version-history.json中")
            sync_readme_to_history(readme_content, latest_version_in_readme, latest_date_in_readme, history_json)
    except Exception as err:
        logger.error(f'验证文件完整性时出错: {err}', exc_info=True)

def sync_readme_to_history(readme_content, version, date, history_json):
    """从README中提取版本信息并同步到version-history.json"""
    logger.info(f"从README.md提取数据并更新version-history.json...")

    # 从README中提取此版本的URL
    section_regex = re.compile(f'\\| {version} \\| {date} \\| (.*?) \\| (.*?) \\| (.*?) \\|')
    section_match = section_regex.search(readme_content)

    if not section_match:
        logger.warning(f"在README.md中找不到版本 {version} 的部分")
        return

    mac_section = section_match.group(1)
    windows_section = section_match.group(2)
    linux_section = section_match.group(3)

    platforms = {}
    platform_count = 0

    # 解析所有平台链接
    for section, section_name in [(mac_section, "Mac"),
                                 (windows_section, "Windows"),
                                 (linux_section, "Linux")]:
        if section and section != 'Not Ready':
            links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', section)
            if links:
                for platform, url in links:
                    platforms[platform] = url
                    platform_count += 1

    # 将条目添加到版本历史
    if platforms:
        new_entry = {
            "version": version,
            "date": date,
            "platforms": platforms
        }

        history_json["versions"].append(new_entry)

        # 排序并保存
        history_json["versions"].sort(key=lambda x: x["version"], reverse=True)

        # 保存更新的历史
        save_version_history(history_json)
        logger.info(f"成功从README.md同步版本 {version}，包含 {platform_count} 个平台链接")
    else:
        logger.warning(f"无法提取版本 {version} 的平台链接")

# 导出函数以进行测试
__all__ = [
    'fetch_latest_download_url',
    'update_readme',
    'read_version_history',
    'save_version_history',
    'extract_version',
    'format_date',
    'get_utc8_time',
    'main'
]

# 运行更新
if __name__ == "__main__":
    import asyncio

    try:
        asyncio.run(main())
    except Exception as error:
        logger.critical(f'未处理的错误: {error}', exc_info=True)
        exit(1)