import argparse
import csv
import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.corruptor import Corruptor
from src.services.harness import Harness

_CSV_FIELDS = ['file', 'format', 'label', 'score', 'time_ms', 'true_label', 'correct']
_CSV_FIELDS_VERBOSE = _CSV_FIELDS + ['crc_score', 'structural_score', 'statistical_score', 'ml_score']


def _to_csv_row(result: dict, verbose: bool) -> dict:
    row = {
        'file': result['file'],
        'format': result['format'],
        'label': result['label'],
        'score': result['score'],
        'time_ms': round(result['time_ms']),
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


def _format_line(result: dict) -> str:
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


def _print_verbose(result: dict) -> None:
    for d in result['detectors']:
        if d['applicable']:
            print(f"    {d['detector']}: score={d['score']:.4f} conf={d['confidence']} [{d['label']}]")
        else:
            print(f"    {d['detector']}: не применим")


def _write_csv(results: list[dict], csv_path: Path, verbose: bool) -> None:
    fields = _CSV_FIELDS_VERBOSE if verbose else _CSV_FIELDS
    with csv_path.open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter=';')
        writer.writeheader()
        for result in results:
            writer.writerow(_to_csv_row(result, verbose))


def run_detect(args: argparse.Namespace) -> None:
    path = Path(args.path)
    if not path.exists():
        print(f"Ошибка: {path} не найден", file=sys.stderr)
        sys.exit(1)

    harness = Harness()
    csv_mode = bool(args.csv)

    if csv_mode and Path(args.csv).is_dir():
        print(f"Ошибка: --csv должен быть путём к файлу, а не директории: {args.csv}", file=sys.stderr)
        sys.exit(1)

    if path.is_file():
        result = harness.analyze_file(path)
        if csv_mode:
            _write_csv([result], Path(args.csv), args.verbose)
        else:
            print(_format_line(result))
            if args.verbose:
                _print_verbose(result)

    else:
        gt = Path(args.ground_truth) if args.ground_truth else None
        output = harness.analyze_directory(path, gt)
        files = output['files']

        if csv_mode:
            _write_csv(files, Path(args.csv), args.verbose)
        else:
            for result in files:
                print(_format_line(result))
                if args.verbose:
                    _print_verbose(result)

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


def run_corrupt(args: argparse.Namespace) -> None:
    sample_dir = Path(args.sample)
    output_dir = Path(args.output)

    if not sample_dir.exists():
        print(f"Ошибка: {sample_dir} не найден", file=sys.stderr)
        sys.exit(1)

    gt_path = Path(args.ground_truth) if args.ground_truth else output_dir / 'ground_truth.json'

    corruptor = Corruptor(seed=42)
    print(f"Исходная выборка: {sample_dir}")
    print(f"Выходная директория: {output_dir}")

    records = corruptor.corrupt_sample(sample_dir=sample_dir, output_dir=output_dir)

    gt_path.parent.mkdir(parents=True, exist_ok=True)
    gt_path.write_text(
        json.dumps([asdict(r) for r in records], ensure_ascii=False, indent=2),
        encoding='utf-8',
    )

    print(f"Создано повреждённых файлов: {len(records)}")
    print(f"Ground truth сохранён: {gt_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog='bench',
        description='Исследовательский стенд оценки уровня целостности файлов',
    )
    sub = parser.add_subparsers(dest='command', required=True)

    p_detect = sub.add_parser('detect', help='Анализ уровня целостности файлов')
    p_detect.add_argument('path', help='Путь к файлу или директории')
    p_detect.add_argument('--ground-truth', metavar='FILE', help='Путь к ground_truth.json')
    p_detect.add_argument('--verbose', action='store_true', help='Показать детали каждого детектора')
    p_detect.add_argument('--csv', metavar='FILE', help='Сохранить отчёт в CSV (вывод в терминал отключается)')

    p_corrupt = sub.add_parser('corrupt', help='Повреждение файлов выборки')
    p_corrupt.add_argument('sample', help='Директория с исходными файлами')
    p_corrupt.add_argument('output', help='Директория для повреждённых файлов')
    p_corrupt.add_argument('--ground-truth', metavar='FILE',
                           help='Куда сохранить ground_truth.json (по умолчанию: output/ground_truth.json)')

    args = parser.parse_args()

    if args.command == 'detect':
        run_detect(args)
    elif args.command == 'corrupt':
        run_corrupt(args)


if __name__ == '__main__':
    main()
