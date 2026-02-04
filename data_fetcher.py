import os
import requests
import patoolib
from pathlib import Path

def download_and_extract_zip(url: str, extract_to: Path) -> list[Path]:
    """下载 ZIP 并用 patool（调用 WinRAR）解压，返回解压后的 CSV 文件列表"""
    extract_to.mkdir(parents=True, exist_ok=True)
    zip_path = extract_to / "temp_data.zip"

    # 下载
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(zip_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    # 解压（使用系统解压工具，如 WinRAR）
    try:
        patoolib.extract_archive(str(zip_path), outdir=str(extract_to))
    except Exception as e:
        raise RuntimeError(f"解压失败: {e}")

    # 清理 ZIP
    zip_path.unlink()

    # 返回所有 CSV
    return sorted(extract_to.glob("*.csv"))