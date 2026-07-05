import json
import sys
from collections import defaultdict
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import REPORTS_DIR, SAMPLE_DIR
from src.core.features.ml_features import FEATURE_NAMES, extract_features
from src.core.format_specs import EXT_TO_HINT, FORMAT_SPECS

MODELS_DIR = Path(__file__).parent.parent / 'models'

def collect_samples() -> list[tuple[str, str, str, str | None]]:
    samples: list[tuple[str, str, str, str | None]] = []

    for f in SAMPLE_DIR.rglob('*'):
        if not f.is_file() or f.name.startswith('.'):
            continue
        hint = EXT_TO_HINT.get(f.suffix.lower())
        if hint is None:
            if f.suffix != '':
                continue
            hint = 'macho'
        samples.append((str(f), 'intact', hint, None))

    gt_path = REPORTS_DIR / 'ground_truth.json'
    if not gt_path.exists():
        print(f'ground_truth.json не найден: {gt_path}', file=sys.stderr)
        sys.exit(1)

    records = json.loads(gt_path.read_text(encoding='utf-8'))
    for rec in records:
        path = Path(rec['corrupted_path'])
        if not path.exists():
            continue
        hint = EXT_TO_HINT.get(path.suffix.lower())
        if hint is None:
            hint = 'macho'
        samples.append((str(path), rec['label'], hint, rec.get('corruption_type')))

    return samples


def main() -> None:
    MODELS_DIR.mkdir(exist_ok=True)

    print('Сбор файлов...')
    samples = collect_samples()
    print(f'Всего файлов: {len(samples)}')

    groups: dict[str, list[tuple[list[float], str, str | None]]] = defaultdict(list)
    skipped = 0

    for file_path, label, hint, corruption_type in samples:
        spec = FORMAT_SPECS.get(hint)
        if spec is None or spec.ml_group is None:
            continue
        try:
            data = Path(file_path).read_bytes()
            features = extract_features(data)
        except Exception as e:
            print(f'  пропуск {file_path}: {e}')
            skipped += 1
            continue
        if corruption_type == 'truncate':
            continue
        groups[spec.ml_group].append((features, label, corruption_type))

    if skipped:
        print(f'Пропущено файлов: {skipped}')

    for group_name, data_pairs in groups.items():
        X = np.array([f for f, _, _ in data_pairs])
        y = np.array([lbl for _, lbl, _ in data_pairs])

        counts = {lbl: int(np.sum(y == lbl)) for lbl in np.unique(y)}
        print(f'\nГруппа [{group_name}]: {len(y)} сэмплов — {counts}')

        intact_idx = [i for i, (_, lbl, _) in enumerate(data_pairs) if lbl == 'intact']
        n_intact = len(intact_idx)

        by_type: dict[str, list[int]] = defaultdict(list)
        for i, (_, lbl, ctype) in enumerate(data_pairs):
            if lbl == 'corrupted':
                by_type[ctype or 'unknown'].append(i)

        total_corrupted = sum(len(v) for v in by_type.values())
        if total_corrupted > n_intact:
            rng = np.random.default_rng(42)
            n_types = len(by_type)
            per_type = n_intact // n_types
            corrupted_idx: list[int] = []
            for ctype, idxs in by_type.items():
                take = min(per_type, len(idxs))
                corrupted_idx += list(rng.choice(idxs, size=take, replace=False))
            balanced_idx = intact_idx + corrupted_idx
            X = X[balanced_idx]
            y = y[balanced_idx]
            type_counts = {t: min(per_type, len(v)) for t, v in by_type.items()}
            print(f'  даунсэмплинг: {len(data_pairs)} → {len(balanced_idx)} сэмплов (1:1)')
            print(f'  типы повреждений: {type_counts}')

        clf = RandomForestClassifier(
            n_estimators=100,
            max_depth=None,
            min_samples_leaf=2,
            random_state=42,
        )

        cv_scores = cross_val_score(clf, X, y, cv=min(5, len(y) // 2), scoring='accuracy')
        print(f'  CV accuracy: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}')

        clf.fit(X, y)

        importances = sorted(
            zip(FEATURE_NAMES, clf.feature_importances_),
            key=lambda t: t[1], reverse=True,
        )
        print('  Топ признаки:', ', '.join(f'{n}={v:.3f}' for n, v in importances[:4]))

        out_path = MODELS_DIR / f'{group_name}.pkl'
        joblib.dump(clf, out_path)
        print(f'  Модель сохранена: {out_path}')

    print('\nГотово.')


if __name__ == '__main__':
    main()
