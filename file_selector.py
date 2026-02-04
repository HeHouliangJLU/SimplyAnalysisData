# file_selector.py
import re
from datetime import datetime
from pathlib import Path
from datetime import datetime, timedelta          # ← 添加 timedelta

def parse_filename_time(filename: str) -> tuple[datetime, datetime]:
    """从 data_YYYYMMDD_YYYYMMDD.csv 提取时间范围"""
    stem = filename.replace('.csv', '')
    matches = re.findall(r'\d{8}', stem)
    if len(matches) >= 2:
        start = datetime.strptime(matches[0], "%Y%m%d")
        end = datetime.strptime(matches[1], "%Y%m%d") + timedelta(days=1)
        return start, end
    else:
        raise ValueError(f"无法解析文件名中的时间: {filename}")

def select_files_in_range(csv_dir: Path, start_dt: datetime, end_dt: datetime) -> list[Path]:
    csv_files = sorted(csv_dir.glob("*.csv"))
    selected = []
    for f in csv_files:
        f_start, f_end = parse_filename_time(f.name)
        if f_end > start_dt and f_start < end_dt:
            selected.append(f)
    return selected