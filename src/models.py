from dataclasses import dataclass


@dataclass
class CorruptionRecord:
    original_path: str
    corrupted_path: str
    corruption_type: str
    position: str
    ratio: float
    label: str = 'corrupted'