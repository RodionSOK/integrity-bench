"""Собирает eval_sample: 2 целых из test_sample + 2 повреждённых из test_corrupted на каждый формат."""
import json
import random
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.format_specs import EXT_TO_HINT

SAMPLE_DIR    = Path('test_sample')
CORRUPTED_DIR = Path('test_corrupted')
GT_SOURCE     = Path('test_reports') / 'ground_truth.json'
EVAL_DIR      = Path('eval_sample')
GT_OUT        = Path('eval_ground_truth.json')

N_INTACT    = 2
N_CORRUPTED = 2
SEED        = 42


def collect_by_format(directory: Path) -> dict[str, list[Path]]:
    by_fmt: dict[str, list[Path]] = {}
    for f in directory.rglob('*'):
        if not f.is_file() or f.name.startswith('.'):
            continue
        hint = EXT_TO_HINT.get(f.suffix.lower())
        if hint is None:
            hint = 'macho' if f.suffix == '' else None
        if hint is None:
            continue
        by_fmt.setdefault(hint, []).append(f)
    return by_fmt


def main() -> None:
    rng = random.Random(SEED)

    gt_records = json.loads(GT_SOURCE.read_text(encoding='utf-8'))
    corrupted_labels = {Path(r['corrupted_path']).name: r for r in gt_records}

    if EVAL_DIR.exists():
        shutil.rmtree(EVAL_DIR)
    EVAL_DIR.mkdir()

    intact_by_fmt   = collect_by_format(SAMPLE_DIR)
    corrupted_by_fmt = collect_by_format(CORRUPTED_DIR)

    ground_truth = []

    all_formats = sorted(set(intact_by_fmt) | set(corrupted_by_fmt))
    for fmt in all_formats:
        intact_files   = intact_by_fmt.get(fmt, [])
        corrupted_files = corrupted_by_fmt.get(fmt, [])

        if len(intact_files) < N_INTACT or len(corrupted_files) < N_CORRUPTED:
            print(f'  {fmt}: недостаточно файлов, пропуск')
            continue

        for src in rng.sample(intact_files, N_INTACT):
            dst = EVAL_DIR / f'intact-{fmt}-{src.name}'
            shutil.copy2(src, dst)
            ground_truth.append({'file': dst.name, 'label': 'intact', 'format': fmt})

        for src in rng.sample(corrupted_files, N_CORRUPTED):
            dst = EVAL_DIR / f'corrupted-{fmt}-{src.name}'
            shutil.copy2(src, dst)
            rec = corrupted_labels.get(src.name, {})
            ground_truth.append({
                'file': dst.name,
                'label': 'corrupted',
                'format': fmt,
                'corruption_type': rec.get('corruption_type', ''),
            })

    GT_OUT.write_text(
        json.dumps(ground_truth, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )

    intact_n   = sum(1 for r in ground_truth if r['label'] == 'intact')
    corrupted_n = sum(1 for r in ground_truth if r['label'] == 'corrupted')
    print(f'Готово: {len(ground_truth)} файлов — intact: {intact_n}, corrupted: {corrupted_n}')
    print(f'Директория: {EVAL_DIR}')
    print(f'Ground truth: {GT_OUT}')


if __name__ == '__main__':
    main()
