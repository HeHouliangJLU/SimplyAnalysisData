import json
from pathlib import Path

def save_results(results: dict, output_dir: Path):
    output_dir.mkdir(exist_ok=True)
    with open(output_dir / "analysis_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"✅ 结果已保存至 {output_dir}")