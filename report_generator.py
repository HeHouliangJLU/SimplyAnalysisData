# report_generator.py
import json
from pathlib import Path

def save_report(report: dict, output_path: Path):
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"📄 报告已保存: {output_path}")

def print_summary(report: dict):
    cols = list(report["column_reports"].keys())
    print("\n=== 全局摘要 ===")
    print(f"总数据点: {report['global_summary']['total_data_points']}")
    print(f"处理时间段: {report['global_summary']['processing_time_range']}")
    print(f"列数: {len(cols)}")

    # 打印前3列示例
    for col in cols[:3]:
        r = report["column_reports"][col]
        print(f"\n【{col}】")
        print(f"  均值: {r['mean']:.3f}")
        print(f"  最大值: {r['max_value']:.3f} @ {r['max_time']}")
        print(f"  最小值: {r['min_value']:.3f} @ {r['min_time']}")
        print(f"  斜率: {r['slope']:.6f}")