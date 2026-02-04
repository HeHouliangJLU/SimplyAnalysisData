# main.py
import json
from datetime import datetime
from pathlib import Path

from file_selector import select_files_in_range
from stream_processor import read_csv_chunks, init_accumulator, update_accumulator, finalize_stats
from report_generator import save_report, print_summary
from visualizer import plot_boxplot_with_mean, plot_stat_bars


def sample_time_series_for_plotting(csv_files, start_time, end_time, top_k=5):
    """
    （可选）为绘图采样原始时间序列数据（仅对波动最大的 top_k 列）
    返回: List[{
        "col": str,
        "times": List[str],
        "values": List[float],
        "min_time": str, "min_value": float,
        "max_time": str, "max_value": float,
        "slope": float
    }]
    """
    # 为简化，此处跳过；实际可基于 global_acc 的 y_vals_list 和 min/max_time 构造
    return []


def main():
    # ====== 用户配置 ======
    CSV_DIR = Path("simulated_data")          # CSV 文件所在目录
    OUTPUT_DIR = Path("analysis_output")
    START_TIME = datetime(2025, 1, 10, 0, 0, 0)
    END_TIME = datetime(2025, 2, 20, 23, 59, 59)

    OUTPUT_DIR.mkdir(exist_ok=True)

    # 选择文件
    selected_files = select_files_in_range(CSV_DIR, START_TIME, END_TIME)
    if not selected_files:
        print("❌ 未找到匹配时间段的 CSV 文件")
        return

    print(f"🔍 选中 {len(selected_files)} 个文件进行处理")

    # 从第一个文件获取列名（跳过前3行）
    first_file = selected_files[0]
    try:
        sample_df = next(read_csv_chunks(first_file, chunksize=1))
        col_names = sample_df.columns[1:].tolist()  # 排除 timestamp 列
    except StopIteration:
        raise ValueError(f"文件 {first_file} 为空或格式错误")

    print(f"📊 检测到 {len(col_names)} 个数据列")

    # 初始化全局累加器
    global_acc = init_accumulator(n_cols=len(col_names), col_names=col_names)

    all_segment_reports = []

    # 分段处理：每个文件作为一个 segment
    for idx, csv_file in enumerate(selected_files):
        print(f"\n🔄 处理文件 {idx+1}/{len(selected_files)}: {csv_file.name}")

        # 为当前 segment 初始化累加器
        seg_acc = init_accumulator(n_cols=len(col_names), col_names=col_names)

        # 流式读取并更新
        for chunk in read_csv_chunks(csv_file, chunksize=10000):
            seg_acc = update_accumulator(seg_acc, chunk, START_TIME, END_TIME)
            global_acc = update_accumulator(global_acc, chunk, START_TIME, END_TIME)

        # 生成分段报告
        seg_report = finalize_stats(seg_acc)
        seg_report["segment_info"] = {"file": csv_file.name}
        all_segment_reports.append(seg_report)

        # 保存分段 JSON 报告
        seg_json_path = OUTPUT_DIR / f"segment_{idx+1:02d}_{csv_file.stem}_report.json"
        save_report(seg_report, seg_json_path)

        # === 可视化：分段箱形图 ===
        # 构造箱形图所需数据（使用采样的 y_vals_list）
        box_data = {}
        for j, name in enumerate(seg_acc["col_names"]):
            vals = seg_acc["y_vals_list"][j]
            if len(vals) > 0:
                box_data[name] = vals

        if box_data:
            plot_boxplot_with_mean(
                data_dict=box_data,
                title=f"分段 {idx+1}: {csv_file.stem} 数据分布",
                save_path=OUTPUT_DIR / f"segment_{idx+1:02d}_boxplot.png"
            )

    # === 全局报告 ===
    global_report = finalize_stats(global_acc)
    global_report["global_summary"].update({
        "total_files_processed": len(selected_files),
        "processing_time_range": f"{START_TIME.isoformat()} to {END_TIME.isoformat()}"
    })

    # 保存全局 JSON
    global_json_path = OUTPUT_DIR / "GLOBAL_ANALYSIS_REPORT.json"
    save_report(global_report, global_json_path)

    # === 全局可视化 ===
    # 1. 全局箱形图
    global_box_data = {}
    for j, name in enumerate(global_acc["col_names"]):
        vals = global_acc["y_vals_list"][j]
        if len(vals) > 0:
            global_box_data[name] = vals

    if global_box_data:
        plot_boxplot_with_mean(
            data_dict=global_box_data,
            title="全局数据分布（所有分段合并）",
            save_path=OUTPUT_DIR / "global_boxplot.png"
        )

    # 2. 统计指标柱状图
    plot_stat_bars(global_report, OUTPUT_DIR / "global_statistics_bars.png")

    # 3. （可选）时间序列图 —— 需要额外采样逻辑，此处暂略

    # 打印摘要
    print_summary(global_report)

    print(f"\n✅ 所有报告和图表已保存至: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()