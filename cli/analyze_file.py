import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))  # для запуска через python cmd/...

from src.services.harness import Harness

_CSV_FIELDS = ['file', 'format', 'label', 'score', 'time_ms', 'true_label', 'correct']
_CSV_FIELDS_VERBOSE = _CSV_FIELDS + ['crc_score', 'structural_score', 'statistical_score', 'ml_score']


def _to_csv_row(result: dict, verbose: bool) -> dict:
    row = {
        'file': result['file'],
        'format': result['format'],
        'label': result['label'],
        'score': result['score'],
        'time_ms': round(result['time_ms'], 1),
        'true_label': result.get('true_label', ''),
        'correct': result.get('correct', ''),
    }
    if verbose:
        by_name = {d['detector']: d for d in result['detectors']}
        for key, det in (('crc_score', 'CrcDetector'),
                         ('structural_score', 'StructuralDetector'),
                         ('statistical_score', 'StatisticalDetector'),
                         ('ml_score', 'MlDetector')):
            d = by_name.get(det)
            row[key] = round(d['score'], 4) if d and d['applicable'] else ''
    return row


def format_line(result: dict) -> str:
    name = Path(result['file']).name
    label = result['label']
    score = result['score']
    fmt = result['format']
    time_ms = result['time_ms']
    marker = '!' if label in ('corrupted', 'uncertain') else ' '
    line = f"{marker} {name:<40}  {label:<10}  {score:.4f}  [{fmt}]  {time_ms:.1f}мс"
    if 'true_label' in result:
        mark = '+' if result.get('correct') else '-'
        line += f"  gt:{result['true_label']} {mark}"
    return line


def print_verbose(result: dict) -> None:
    for d in result['detectors']:
        if d['applicable']:
            print(f"    {d['detector']}: score={d['score']:.4f} conf={d['confidence']} [{d['label']}]")
        else:
            print(f"    {d['detector']}: не применим")


def write_csv(results: list[dict], csv_path: Path, verbose: bool) -> None:
    fields = _CSV_FIELDS_VERBOSE if verbose else _CSV_FIELDS
    with csv_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for result in results:
            writer.writerow(_to_csv_row(result, verbose))


def main() -> None:
    parser = argparse.ArgumentParser(description='Оценка уровня целостности файла')
    parser.add_argument('path', help='Путь к файлу или директории')
    parser.add_argument('--ground-truth', help='Путь к ground_truth.json')
    parser.add_argument('--verbose', action='store_true', help='Показать детали детекторов')
    parser.add_argument('--csv', metavar='FILE', help='Сохранить отчёт в CSV (терминал отключается)')
    args = parser.parse_args()

    path = Path(args.path)
    harness = Harness()
    csv_mode = bool(args.csv)

    if path.is_file():
        result = harness.analyze_file(path)
        if csv_mode:
            write_csv([result], Path(args.csv), args.verbose)
        else:
            print(format_line(result))
            if args.verbose:
                print_verbose(result)

    elif path.is_dir():
        gt = Path(args.ground_truth) if args.ground_truth else None
        output = harness.analyze_directory(path, gt)
        files = output['files']

        if csv_mode:
            write_csv(files, Path(args.csv), args.verbose)
        else:
            for result in files:
                print(format_line(result))
                if args.verbose:
                    print_verbose(result)

            metrics = output.get('metrics', {})
            problem = [r for r in files if r['label'] in ('corrupted', 'uncertain')]
            corrupted = sum(1 for r in problem if r['label'] == 'corrupted')
            uncertain = sum(1 for r in problem if r['label'] == 'uncertain')
            print(f"\nИтого: {len(files)} файлов, проблемных: {len(problem)}"
                  f" (corrupted: {corrupted}, uncertain: {uncertain})", end='')
            if metrics:
                print(f", среднее время: {metrics['avg_time_ms']:.1f}мс/файл", end='')
                if 'accuracy' in metrics:
                    print(f", accuracy: {metrics['accuracy']:.2%}"
                          f", precision: {metrics['precision']:.2%}"
                          f", recall: {metrics['recall']:.2%}", end='')
            print()
    else:
        print(f"Ошибка: {path} не найден", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
