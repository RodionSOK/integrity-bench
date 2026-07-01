import csv
from collections import defaultdict
from pathlib import Path

from src.config import REPORTS_DIR

INPUT_CSV = REPORTS_DIR / '2_4_impact_analysis.csv'
OUTPUT_CSV = REPORTS_DIR / '2_4_summary.csv'

FORMAT_GROUPS = {
    '.txt': 'текстовые', '.csv': 'текстовые', '.json': 'текстовые',
    '.elf': 'исполняемые', '.so': 'исполняемые',
    '.exe': 'исполняемые', '.dll': 'исполняемые', '': 'исполняемые',
    '.zip': 'архивы', '.gz': 'архивы', '.gzip': 'архивы', '.7z': 'архивы',
    '.png': 'изображения', '.jpg': 'изображения', '.jpeg': 'изображения', '.bmp': 'изображения',
    '.mp4': 'видео', '.mkv': 'видео', '.avi': 'видео',
}


def get_group(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    return FORMAT_GROUPS.get(ext, 'неизвестно')


def safe_float(val: str) -> float | None:
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def safe_bool(val: str) -> bool | None:
    if val == 'True':
        return True
    if val == 'False':
        return False
    return None


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def main():
    rows = []
    with INPUT_CSV.open(encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    groups = defaultdict(list)
    for row in rows:
        key = (get_group(row['original']), row['corruption_type'])
        groups[key].append(row)

    summary_rows = []
    for (group, ctype), group_rows in sorted(groups.items()):
        orig_entropy = [v for r in group_rows if (v := safe_float(r['orig_entropy'])) is not None]
        corr_entropy = [v for r in group_rows if (v := safe_float(r['corr_entropy'])) is not None]
        orig_var = [v for r in group_rows if (v := safe_float(r['orig_windowed_entropy_variance'])) is not None]
        corr_var = [v for r in group_rows if (v := safe_float(r['corr_windowed_entropy_variance'])) is not None]

        crc_total = [r for r in group_rows if safe_bool(r.get('orig_crc_ok')) is not None]
        crc_failed = [r for r in crc_total if safe_bool(r.get('corr_crc_ok')) is False]

        dec_total = [r for r in group_rows if safe_bool(r.get('orig_decodable')) is not None]
        dec_failed = [r for r in dec_total if safe_bool(r.get('corr_decodable')) is False]

        summary_rows.append({
            'группа': group,
            'тип_повреждения': ctype,
            'файлов': len(group_rows),
            'orig_entropy_mean': round(mean(orig_entropy), 4),
            'corr_entropy_mean': round(mean(corr_entropy), 4),
            'delta_entropy': round(mean(corr_entropy) - mean(orig_entropy), 4),
            'orig_variance_mean': round(mean(orig_var), 6),
            'corr_variance_mean': round(mean(corr_var), 6),
            'delta_variance': round(mean(corr_var) - mean(orig_var), 6),
            'crc_fail_rate': f"{len(crc_failed)}/{len(crc_total)}" if crc_total else '-',
            'decode_fail_rate': f"{len(dec_failed)}/{len(dec_total)}" if dec_total else '-',
        })

    with OUTPUT_CSV.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"Готово. Результат: {OUTPUT_CSV}")


if __name__ == '__main__':
    main()