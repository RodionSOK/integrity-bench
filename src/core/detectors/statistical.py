import time
from pathlib import Path

from src.core.detectors.base import Detector, DetectorResult, _label
from src.core.features.universal import compute_entropy, compute_windowed_entropy_variance
from src.core.format_specs import FORMAT_SPECS

CONFIDENCE = 0.3
_DEFAULT_STAT = (0.0, 8.0)  


def _variance_score(v: float, v_low: float, v_high: float) -> float:
    if v <= v_low:
        if v_low == 0.0:
            return 1.0
        return max(0.0, v / v_low)
    if v <= v_high:
        return 1.0
    if v_high == 0.0:
        return 0.0
    return max(0.0, 1.0 - (v - v_high) / (2.0 * v_high))


class StatisticalDetector(Detector):
    def analyze(self, data: bytes, format_hint: str, _file_path: Path | None = None) -> DetectorResult:
        t0 = time.perf_counter()
        entropy = compute_entropy(data)
        variance = compute_windowed_entropy_variance(data)

        spec = FORMAT_SPECS.get(format_hint)
        v_low, v_high = (
            (spec.statistical.v_low, spec.statistical.v_high)
            if spec is not None and spec.statistical is not None
            else _DEFAULT_STAT
        )

        score = _variance_score(variance, v_low, v_high)

        return DetectorResult(
            score=score,
            label=_label(score),
            confidence=CONFIDENCE,
            signals={
                'entropy': round(entropy, 4),
                'windowed_entropy_variance': round(variance, 4),
                'v_low': v_low,
                'v_high': v_high,
            },
            time_ms=(time.perf_counter() - t0) * 1000,
            applicable=True,
        )
