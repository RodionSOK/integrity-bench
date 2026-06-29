import json
from dataclasses import asdict

from src.corruptor import Corruptor
from src.config import SAMPLE_DIR, CORRUPTED_DIR, REPORTS_DIR


def main():
    corruptor = Corruptor(seed=42)

    print(f"Исходная выборка: {SAMPLE_DIR}")
    print(f"Выходная директория: {CORRUPTED_DIR}")

    records = corruptor.corrupt_sample(
        sample_dir=SAMPLE_DIR,
        output_dir=CORRUPTED_DIR,
    )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ground_truth = [asdict(r) for r in records]
    (REPORTS_DIR / 'ground_truth.json').write_text(
        json.dumps(ground_truth, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )

    print(f"Создано повреждённых файлов: {len(records)}")
    print(f"Ground truth сохранён: {REPORTS_DIR / 'ground_truth.json'}")


if __name__ == '__main__':
    main()