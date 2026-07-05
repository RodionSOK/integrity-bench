import time
from pathlib import Path

from src.core.detectors.base import Detector, DetectorResult, _label, _not_applicable
from src.core.features.ml_features import extract_features
from src.core.format_specs import FORMAT_SPECS

CONFIDENCE = 0.9
_MODELS_DIR = Path(__file__).parent.parent.parent.parent / 'models'


class MlDetector(Detector):
    def __init__(self) -> None:
        self._models: dict = {}
        if _MODELS_DIR.exists():
            self._load_models()

    def _load_models(self) -> None:
        try:
            import joblib
        except ImportError:
            return
        for pkl in _MODELS_DIR.glob('*.pkl'):
            self._models[pkl.stem] = joblib.load(pkl)

    def analyze(self, data: bytes, format_hint: str, file_path: Path | None = None) -> DetectorResult:
        spec = FORMAT_SPECS.get(format_hint)
        if spec is None or spec.ml_group is None:
            return _not_applicable()

        model = self._models.get(spec.ml_group)
        if model is None:
            return _not_applicable()

        t0 = time.perf_counter()
        features = extract_features(data)
        proba = model.predict_proba([features])[0]

        classes = list(model.classes_)
        intact_idx = classes.index('intact') if 'intact' in classes else 1
        score = float(proba[intact_idx])

        return DetectorResult(
            score=score,
            label=_label(score),
            confidence=CONFIDENCE,
            signals={'ml_group': spec.ml_group, 'p_intact': round(score, 4)},
            time_ms=(time.perf_counter() - t0) * 1000,
            applicable=True,
        )
