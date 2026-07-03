import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.harness import Harness


def print_result(result: dict) -> None:
    print(f"\n{result['file']}  [{result['format']}]")
    print(f"  score={result['score']:.4f}  label={result['label']}  время={result['time_ms']:.1f}мс")
    for d in result['detectors']:
        if d['applicable']:
            print(f"  {d['detector']}: score={d['score']:.4f} conf={d['confidence']} [{d['label']}]")
        else:
            print(f"  {d['detector']}: не применим")
    if 'true_label' in result:
        mark = '+' if result.get('correct') else '-'
        print(f"  ground truth: {result['true_label']} {mark}")


def main() -> None:
    parser = argparse.ArgumentParser(description='Оценка уровня целостности файла')
    parser.add_argument('path', help='Путь к файлу или директории')
    parser.add_argument('--ground-truth', help='Путь к ground_truth.json')
    args = parser.parse_args()

    path = Path(args.path)
    harness = Harness()

    if path.is_file():
        print_result(harness.analyze_file(path))

    elif path.is_dir():
        gt = Path(args.ground_truth) if args.ground_truth else None
        output = harness.analyze_directory(path, gt)
        for result in output['files']:
            print_result(result)
        metrics = output.get('metrics', {})
        if metrics:
            print(f"\nИтого: {metrics['total']} файлов, "
                  f"accuracy={metrics['accuracy']:.2%}, "
                  f"среднее время={metrics['avg_time_ms']:.1f}мс/файл")
    else:
        print(f"Ошибка: {path} не найден", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
