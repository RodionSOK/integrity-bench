import time
from pathlib import Path

from src.core.detectors.base import Detector, DetectorResult, _label, _not_applicable
from src.core.format_specs import FORMAT_SPECS

CONFIDENCE = 0.95


class CrcDetector(Detector):
    def analyze(self, data: bytes, format_hint: str, file_path: Path | None = None) -> DetectorResult:
        spec = FORMAT_SPECS.get(format_hint)
        if spec is None or spec.crc is None:
            return _not_applicable()

        t0 = time.perf_counter()
        signals = spec.crc.checker.check(data)
        score = 1.0 if spec.crc.ok_fn(signals) else 0.0

        return DetectorResult(
            score=score,
            label=_label(score),
            confidence=CONFIDENCE,
            signals=signals,
            time_ms=(time.perf_counter() - t0) * 1000,
            applicable=True,
        )
