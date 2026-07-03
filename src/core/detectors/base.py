from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DetectorResult:
    score: float
    label: str  
    confidence: float
    signals: dict
    time_ms: float
    applicable: bool


def _not_applicable() -> DetectorResult:
    return DetectorResult(score=0.0, label='uncertain', confidence=0.0, signals={}, time_ms=0.0, applicable=False)


def _label(score: float) -> str:
    if score >= 0.8:
        return 'intact'
    if score <= 0.3:
        return 'corrupted'
    return 'uncertain'


class Detector(ABC):
    @abstractmethod
    def analyze(self, data: bytes, format_hint: str, file_path: Path | None = None) -> DetectorResult:
        ...
