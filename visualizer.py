# visualizer.py
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List


# === 安全设置中文字体（跨平台）===
def set_chinese_font():
    import platform
    system = platform.system()
    try:
        if system == "Windows":
            plt.rcParams['font.sans-serif'] = ['SimHei']
        elif system == "Darwin":  # macOS
            plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang HK', 'Heiti TC']
        else:  # Linux
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'WenQuanYi Micro Hei', 'Noto Sans CJK SC']
        plt.rcParams['axes.unicode_minus'] = False
    except Exception:
        # 如果字体设置失败，禁用中文，避免乱码
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = True
        print("⚠️ 未找到中文字体，图表将使用英文标签")


# 调用一次即可
set_chinese_font()


def plot_boxplot_with_mean(
        data_dict: Dict[str, List[float]],
        title: str,
        save_path: Path
):
    """绘制多列箱形图，并标出均值"""
    df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in data_dict.items()]))

    plt.figure(figsize=(min(20, len(df.columns) * 0.5), 8))
    ax = sns.boxplot(data=df, orient="v")

    # 标出均值
    means = df.mean()
    x_positions = range(len(means))
    ax.scatter(x_positions, means, color='red', marker='^', s=60, zorder=5, label='均值')

    plt.xticks(rotation=90)
    plt.title(title, fontsize=14)
    plt.ylabel("数值")
    plt.legend()
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()


def plot_stat_bars(report: Dict, save_path: Path):
    """绘制均值、标准差、极差的柱状图"""
    cols = list(report["column_reports"].keys())
    means = [report["column_reports"][c]["mean"] for c in cols]
    stds = [report["column_reports"][c]["std"] for c in cols]
    ranges = [
        report["column_reports"][c]["max_value"] - report["column_reports"][c]["min_value"]
        for c in cols
    ]

    fig, axs = plt.subplots(3, 1, figsize=(20, 12))
    for ax, data, title in zip(axs, [means, stds, ranges], ["均值", "标准差", "极差 (Max - Min)"]):
        ax.bar(cols, data, color='skyblue')
        ax.set_xticks(range(len(cols)))
        ax.set_xticklabels(cols, rotation=90)
        ax.set_title(title)
        ax.grid(axis='y', linestyle='--', alpha=0.7)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()


def plot_time_series_with_peaks(
        time_series_data: List[Dict],  # [{col, times, values, min_time, max_time}]
        save_path: Path
):
    """绘制关键列的时间序列 + 峰值标记"""
    n = min(5, len(time_series_data))
    fig, axs = plt.subplots(n, 1, figsize=(15, 3 * n), sharex=True)
    if n == 1:
        axs = [axs]

    for i, item in enumerate(time_series_data[:n]):
        times = pd.to_datetime(item["times"])
        values = item["values"]
        col = item["col"]

        axs[i].plot(times, values, label=col, alpha=0.8)

        # 标记最大值
        max_t = pd.to_datetime(item["max_time"])
        max_v = item["max_value"]
        axs[i].scatter([max_t], [max_v], color='red', s=50, zorder=5, label='最大值')

        # 标记最小值
        min_t = pd.to_datetime(item["min_time"])
        min_v = item["min_value"]
        axs[i].scatter([min_t], [min_v], color='blue', s=50, zorder=5, label='最小值')

        # 拟合直线
        x_num = [t.timestamp() for t in times]
        slope = item.get("slope", 0)
        intercept = np.mean(values) - slope * np.mean(x_num)
        fit_line = [slope * x + intercept for x in x_num]
        axs[i].plot(times, fit_line, '--', color='green', label=f'拟合线 (斜率={slope:.2e})')

        axs[i].set_ylabel(col)
        axs[i].legend(loc='upper right')
        axs[i].grid(True)

    axs[-1].set_xlabel("时间")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
