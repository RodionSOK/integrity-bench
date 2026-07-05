import json
import time
from pathlib import Path

from src.core.detectors.base import Detector, DetectorResult
from src.core.format_specs import EXT_TO_HINT
from src.core.detectors.crc import CrcDetector
from src.core.detectors.ml import MlDetector
from src.core.detectors.statistical import StatisticalDetector
from src.core.detectors.structural import StructuralDetector
from src.services.aggregator import Aggregator


class Harness:
    def __init__(self) -> None:
        self.detectors: list[Detector] = [
            CrcDetector(),
            StructuralDetector(),
            StatisticalDetector(),
            MlDetector(),
        ]
        self.aggregator = Aggregator()

    def _detect_format(self, path: Path) -> str:
        return EXT_TO_HINT.get(path.suffix.lower(), 'unknown')

    def analyze_file(self, path: Path, format_hint: str | None = None) -> dict:
        fmt = format_hint or self._detect_format(path)
        data = path.read_bytes()
        t0 = time.perf_counter()

        results: list[DetectorResult] = [
            det.analyze(data, fmt, path) for det in self.detectors
        ]
        aggregate = self.aggregator.aggregate(results)
        total_ms = (time.perf_counter() - t0) * 1000

        return {
            'file': path.name,
            'format': fmt,
            'score': aggregate['score'],
            'label': aggregate['label'],
            'time_ms': round(total_ms, 2),
            'detectors': [
                {
                    'detector': type(det).__name__,
                    'applicable': r.applicable,
                    'score': round(r.score, 4) if r.applicable else None,
                    'confidence': r.confidence if r.applicable else None,
                    'label': r.label if r.applicable else None,
                    'time_ms': round(r.time_ms, 2),
                    'signals': r.signals,
                }
                for det, r in zip(self.detectors, results)
            ],
        }

    def analyze_directory(
        self,
        directory: Path,
        ground_truth_path: Path | None = None,
    ) -> dict:
        ground_truth: dict[str, str] = {}
        if ground_truth_path is not None:
            records = json.loads(ground_truth_path.read_text(encoding='utf-8'))
            for rec in records:
                name = Path(rec['corrupted_path']).name
                ground_truth[name] = rec['label']

        file_results = []
        for f in sorted(directory.rglob('*')):
            if not f.is_file() or f.name.startswith('.'):
                continue
            result = self.analyze_file(f)
            if f.name in ground_truth:
                result['true_label'] = ground_truth[f.name]
                result['correct'] = result['label'] == ground_truth[f.name]
            file_results.append(result)

        with_gt = [r for r in file_results if 'true_label' in r]
        metrics: dict = {}
        if with_gt:
            correct = sum(1 for r in with_gt if r.get('correct', False))
            tp = sum(1 for r in with_gt if r['label'] == 'corrupted' and r['true_label'] == 'corrupted')
            fp = sum(1 for r in with_gt if r['label'] == 'corrupted' and r['true_label'] == 'intact')
            fn = sum(1 for r in with_gt if r['label'] != 'corrupted' and r['true_label'] == 'corrupted')
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            metrics = {
                'total': len(with_gt),
                'correct': correct,
                'incorrect': len(with_gt) - correct,
                'accuracy': round(correct / len(with_gt), 4),
                'precision': round(precision, 4),
                'recall': round(recall, 4),
                'avg_time_ms': round(
                    sum(r['time_ms'] for r in with_gt) / len(with_gt), 2
                ),
            }

        return {'files': file_results, 'metrics': metrics}
