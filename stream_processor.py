# stream_processor.py
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path                         # ← 添加 Path

def read_csv_chunks(file_path: Path, chunksize: int = 10000):
    """跳过前3行，逐块读取"""
    yield from pd.read_csv(file_path, skiprows=2, chunksize=chunksize)

def init_accumulator(n_cols: int, col_names: List[str]) -> Dict[str, Any]:
    return {
        "count": 0,
        "mean": np.zeros(n_cols),
        "M2": np.zeros(n_cols),
        "min_val": np.full(n_cols, np.inf),
        "max_val": np.full(n_cols, -np.inf),
        "min_time": [None] * n_cols,
        "max_time": [None] * n_cols,
        "x_vals": [],  # 时间戳（用于斜率）
        "y_vals_list": [[] for _ in range(n_cols)],  # 每列采样值（限内存）
        "col_names": col_names,
        "total_rows": 0
    }

def update_accumulator(acc: Dict, df_chunk: pd.DataFrame, start_time, end_time) -> Dict:
    # 过滤时间范围（精确到行）
    time_col = pd.to_datetime(df_chunk.iloc[:, 0])
    mask = (time_col >= start_time) & (time_col <= end_time)
    df_filtered = df_chunk[mask]
    if df_filtered.empty:
        return acc

    values = df_filtered.iloc[:, 1:].values  # (n, cols)
    timestamps = time_col[mask].tolist()
    n_rows, n_cols = values.shape

    for i in range(n_rows):
        t = timestamps[i]
        row = values[i]
        for j in range(n_cols):
            x = row[j]

            # 更新 min / max + 时间
            if x < acc["min_val"][j]:
                acc["min_val"][j] = x
                acc["min_time"][j] = t
            if x > acc["max_val"][j]:
                acc["max_val"][j] = x
                acc["max_time"][j] = t

            # Welford 增量统计
            old_mean = acc["mean"][j]
            acc["count"] += 1 if j == 0 else 0  # count 全局共享（实际应 per-col，但近似）
            delta = x - old_mean
            acc["mean"][j] += delta / (acc["total_rows"] + i + 1)
            delta2 = x - acc["mean"][j]
            acc["M2"][j] += delta * delta2

        # 为斜率采样（限制总数）
        if len(acc["x_vals"]) < 5000:
            acc["x_vals"].append(t.timestamp())
            for j in range(n_cols):
                if len(acc["y_vals_list"][j]) < 5000:
                    acc["y_vals_list"][j].append(row[j])

    acc["total_rows"] += n_rows
    return acc

def finalize_stats(acc: Dict) -> Dict[str, Any]:
    n_cols = len(acc["col_names"])
    count = acc["total_rows"]
    variance = np.divide(acc["M2"], count - 1, out=np.zeros_like(acc["M2"]), where=(count > 1))
    std = np.sqrt(variance)
    three_sigma_upper = acc["mean"] + 3 * std
    three_sigma_lower = acc["mean"] - 3 * std

    # 计算每列斜率
    slopes = []
    for j in range(n_cols):
        if len(acc["x_vals"]) > 1 and len(acc["y_vals_list"][j]) > 1:
            slope, _ = np.polyfit(acc["x_vals"], acc["y_vals_list"][j], 1)
        else:
            slope = 0.0
        slopes.append(float(slope))

    # 构建每列报告
    column_reports = {}
    for j, name in enumerate(acc["col_names"]):
        column_reports[name] = {
            "mean": float(acc["mean"][j]),
            "std": float(std[j]),
            "3sigma_upper": float(three_sigma_upper[j]),
            "3sigma_lower": float(three_sigma_lower[j]),
            "min_value": float(acc["min_val"][j]),
            "min_time": acc["min_time"][j].isoformat() if acc["min_time"][j] else None,
            "max_value": float(acc["max_val"][j]),
            "max_time": acc["max_time"][j].isoformat() if acc["max_time"][j] else None,
            "slope": slopes[j],
            "total_points": count
        }

    return {
        "column_reports": column_reports,
        "global_summary": {
            "total_files_processed": 0,  # 由主控填充
            "total_data_points": count,
            "processing_time_range": None  # 由主控填充
        }
    }