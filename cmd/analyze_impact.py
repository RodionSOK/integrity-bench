import csv
import json
from pathlib import Path

import src.core.features.formats
from src.config import REPORTS_DIR
from src.core.features.registry import get_checker
from src.core.features.formats.video import VideoChecker
from src.core.features.universal import (
    compute_entropy,
    compute_windowed_entropy_variance,
)

GROUND_TRUTH = REPORTS_DIR / 'ground_truth.json'
OUTPUT_CSV = REPORTS_DIR / '2_4_impact_analysis.csv'


def analyze_file(path: Path) -> dict:
    data = path.read_bytes()
    result = {
        'entropy': compute_entropy(data),
        'windowed_entropy_variance': compute_windowed_entropy_variance(data),
    }
    checker = get_checker(path.suffix)
    if checker is not None:
        if isinstance(checker, VideoChecker):
            result.update(checker.check_path(str(path)))
        else:
            result.update(checker.check(data))
    return result


def main():
    records = json.loads(GROUND_TRUTH.read_text(encoding='utf-8'))

    rows = []
    for rec in records:
        original = Path(rec['original_path'])
        corrupted = Path(rec['corrupted_path'])

        if not original.exists() or not corrupted.exists():
            continue

        orig_features = analyze_file(original)
        corr_features = analyze_file(corrupted)

        row = {
            'original': original.name,
            'corrupted': corrupted.name,
            'corruption_type': rec['corruption_type'],
            'position': rec['position'],
            'ratio': rec['ratio'],
        }
        for key, val in orig_features.items():
            row[f'orig_{key}'] = val
        for key, val in corr_features.items():
            row[f'corr_{key}'] = val

        rows.append(row)
        print(f"OK: {corrupted.name}")

    if not rows:
        print("Нет данных для анализа.")
        return

    fieldnames = []
    seen = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)

    for row in rows:
        for field in fieldnames:
            row.setdefault(field, '')
            
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nГотово. Результат: {OUTPUT_CSV}")


if __name__ == '__main__':
    main()