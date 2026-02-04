import os
import csv
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path


def generate_simulated_csv(
        output_dir: Path,
        start_date: datetime,
        end_date: datetime,
        days_per_file: int = 7,
        sample_interval_sec: int = 1,  # 每秒一条记录（可改为10秒等）
        num_columns: int = 50,  # 数据列数（不含时间戳），≤254（+1时间列=255）
        chunk_size: int = 10000  # 每次写入行数，控制内存
):
    """
    生成模拟数据 CSV 文件，用于测试分析脚本。
    """
    assert 1 <= num_columns <= 254, "数据列数必须在 1～254 之间（加上时间戳共 ≤255 列）"

    output_dir.mkdir(parents=True, exist_ok=True)

    current_start = start_date
    file_index = 0

    # 生成列名（模拟传感器名）
    data_headers = [f"sensor_{i:03d}" for i in range(1, num_columns + 1)]
    full_headers = ["timestamp"] + data_headers

    while current_start < end_date:
        file_end = min(current_start + timedelta(days=days_per_file), end_date)
        if file_end <= current_start:
            break

        # 文件名：data_YYYYMMDD_YYYYMMDD.csv
        filename = f"data_{current_start.strftime('%Y%m%d')}_{file_end.strftime('%Y%m%d')}.csv"
        filepath = output_dir / filename

        print(f"📝 生成文件: {filename}")

        total_seconds = int((file_end - current_start).total_seconds())
        total_rows = total_seconds // sample_interval_sec + 1

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # 写入前3行表头（模拟真实系统）
            writer.writerow(["# Data Export from Simulation System"])
            writer.writerow([f"# Time Range: {current_start} to {file_end}"])
            writer.writerow(full_headers)  # 第3行为实际列名

            # 预生成基础时间序列（但不全载入内存）
            base_time = int(current_start.timestamp())
            rows_written = 0

            while rows_written < total_rows:
                # 计算当前块的时间范围
                this_chunk = min(chunk_size, total_rows - rows_written)
                timestamps = [base_time + (rows_written + i) * sample_interval_sec for i in range(this_chunk)]

                # 为每列生成带趋势和噪声的数据
                # 示例：第 j 列 = a_j * t + b_j + c_j * sin(ωt) + noise
                chunk_data = []
                for t in timestamps:
                    row = [datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]]  # 时间字符串
                    for j in range(num_columns):
                        # 线性趋势 + 正弦波动 + 高斯噪声
                        trend = 0.001 * j * (t - base_time)  # 缓慢上升
                        sine = 5.0 * np.sin(2 * np.pi * t / (3600 * 2))  # 2小时周期
                        noise = np.random.normal(0, 1.0)
                        value = 100 + trend + sine + noise
                        row.append(f"{value:.3f}")
                    chunk_data.append(row)

                writer.writerows(chunk_data)
                rows_written += this_chunk

        current_start = file_end
        file_index += 1

    print(f"✅ 共生成 {file_index} 个 CSV 文件，保存至: {output_dir}")


if __name__ == "__main__":
    # ====== 配置参数 ======
    OUTPUT_DIR = Path("simulated_data")
    START_DATE = datetime(2025, 1, 1, 0, 0, 0)
    END_DATE = datetime(2025, 3, 31, 23, 59, 59)  # 3个月数据
    DAYS_PER_FILE = 7  # 每个文件7天
    SAMPLE_INTERVAL_SEC = 10  # 每10秒一条记录（降低数据量）
    NUM_COLUMNS = 100  # 100个数据列（+1时间列 = 101列）

    # 生成
    generate_simulated_csv(
        output_dir=OUTPUT_DIR,
        start_date=START_DATE,
        end_date=END_DATE,
        days_per_file=DAYS_PER_FILE,
        sample_interval_sec=SAMPLE_INTERVAL_SEC,
        num_columns=NUM_COLUMNS,
        chunk_size=5000
    )