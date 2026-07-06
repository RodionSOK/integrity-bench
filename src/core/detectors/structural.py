import time
from pathlib import Path

from src.core.detectors.base import Detector, DetectorResult, _label, _not_applicable
from src.core.format_specs import FORMAT_SPECS


class StructuralDetector(Detector):
    def analyze(self, data: bytes, format_hint: str, file_path: Path | None = None) -> DetectorResult:
        spec = FORMAT_SPECS.get(format_hint)
        if spec is None or spec.structural is None:
            return _not_applicable()

        st = spec.structural
        t0 = time.perf_counter()

        if st.needs_path:
            if file_path is None:
                return _not_applicable()
            signals = st.checker.check_path(str(file_path))
        else:
            signals = st.checker.check(data)

        score = 1.0 if st.ok_fn(signals) else 0.0

        return DetectorResult(
            score=score,
            label=_label(score),
            confidence=st.confidence,
            signals=signals,
            time_ms=(time.perf_counter() - t0) * 1000,
            applicable=True,
        )
