import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

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
PROFILES_CSV = REPORTS_DIR / '2_4_windowed_profiles.csv'

WINDOW_SIZE = 256

FORMAT_MAP = {
    '.txt': 'txt', '.csv': 'csv', '.json': 'json',
    '.so': 'elf', '.exe': 'pe', '': 'macho',
    '.zip': 'zip', '.gz': 'gzip', '.7z': '7z',
    '.png': 'png', '.jpg': 'jpeg', '.bmp': 'bmp',
    '.mp4': 'mp4', '.mkv': 'mkv', '.avi': 'avi',
}


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


def get_format(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    return FORMAT_MAP.get(ext, 'unknown')


def find_damaged_range(orig_data: bytes, corr_data: bytes) -> tuple[int, int]:
    min_len = min(len(orig_data), len(corr_data))
    first = next((i for i in range(min_len) if orig_data[i] != corr_data[i]), None)
    if first is None:
        return (len(corr_data), len(orig_data))
    if len(orig_data) != len(corr_data):
        return (first, first + (len(orig_data) - len(corr_data)))
    last = next((i for i in range(min_len - 1, first - 1, -1) if orig_data[i] != corr_data[i]), first)
    return (first, last + 1)


def compute_profile(data: bytes) -> list[tuple[int, float, int]]:
    arr = np.frombuffer(data, dtype=np.uint8)
    result = []
    for i in range(0, len(arr), WINDOW_SIZE):
        window = arr[i:i + WINDOW_SIZE]
        counts = np.bincount(window, minlength=256)
        probs = counts / len(window)
        probs = probs[probs > 0]
        result.append((i, float(-np.sum(probs * np.log2(probs))), len(window)))
    return result


def select_pairs(rows: list[dict], records: list[dict]) -> list[dict]:
    record_lookup = {Path(r['corrupted_path']).name: r for r in records}
    by_format_type: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        fmt = get_format(row['original'])
        if fmt == 'unknown':
            continue
        orig_var = float(row.get('orig_windowed_entropy_variance') or 0)
        corr_var = float(row.get('corr_windowed_entropy_variance') or 0)
        record = record_lookup.get(row['corrupted'])
        if record is None:
            continue
        by_format_type[(fmt, row['corruption_type'])].append({
            'fmt': fmt,
            'row': row,
            'record': record,
            'delta_var': abs(corr_var - orig_var),
        })
    selected = []
    for items in by_format_type.values():
        items.sort(key=lambda x: (-x['delta_var'], abs(float(x['record']['ratio']) - 0.4)))
        selected.append(items[0])
    return selected


def save_profiles(selected: list[dict]) -> None:
    profile_rows = []
    for item in selected:
        fmt = item['fmt']
        record = item['record']
        orig_path = Path(record['original_path'])
        corr_path = Path(record['corrupted_path'])
        if not orig_path.exists() or not corr_path.exists():
            continue
        orig_data = orig_path.read_bytes()
        corr_data = corr_path.read_bytes()
        damaged_start, damaged_end = find_damaged_range(orig_data, corr_data)
        orig_profile = compute_profile(orig_data)
        corr_profile = compute_profile(corr_data)
        for idx in range(max(len(orig_profile), len(corr_profile))):
            orig_ent = orig_profile[idx][1] if idx < len(orig_profile) else ''
            corr_ent = corr_profile[idx][1] if idx < len(corr_profile) else ''
            win_len = (
                orig_profile[idx][2] if idx < len(orig_profile)
                else corr_profile[idx][2] if idx < len(corr_profile)
                else ''
            )
            profile_rows.append({
                'format': fmt,
                'original': orig_path.name,
                'corrupted': corr_path.name,
                'corruption_type': record['corruption_type'],
                'ratio': record['ratio'],
                'window_size': WINDOW_SIZE,
                'damaged_start': damaged_start,
                'damaged_end': damaged_end,
                'window_index': idx,
                'window_offset_bytes': idx * WINDOW_SIZE,
                'window_length_bytes': win_len,
                'entropy_original': orig_ent,
                'entropy_corrupted': corr_ent,
            })
        print(f"Профиль: {fmt} ({corr_path.name})")
    with PROFILES_CSV.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(profile_rows[0].keys()))
        writer.writeheader()
        writer.writerows(profile_rows)
    print(f"Профили: {PROFILES_CSV}")


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

    selected = select_pairs(rows, records)
    save_profiles(selected)


if __name__ == '__main__':
    main()
