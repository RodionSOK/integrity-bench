from pathlib import Path
from src.models import CorruptionRecord
from src.types import CorruptionType, Position
import random


def _compute_range(size: int, ratio: float, position: Position) -> tuple[int, int]:
    length = max(1, int(size * ratio))
    if position == 'start':
        start = 0
    elif position == 'end':
        start = max(0, size - length)
    elif position == 'middle':
        start = (size - length) // 2
    else:
        start = random.randint(0, max(0, size - length))
    return start, min(size, start + length)


def corrupt_bytes(
    data: bytes,
    corruption_type: CorruptionType,
    position: Position,
    ratio: float,
) -> bytes:
    if not data:
        return data
    start, end = _compute_range(len(data), ratio, position)
    if corruption_type == 'truncate':
        return data[:start] + data[end:]
    buf = bytearray(data)
    if corruption_type == 'zero_fill':
        buf[start:end] = bytes(end - start)
    else:
        buf[start:end] = random.randbytes(end - start)
    return bytes(buf)


class Corruptor:
    def __init__(self, seed: int | None = None):
        if seed is not None:
            random.seed(seed)

    def corrupt_file(
        self,
        src: Path,
        dst: Path,
        corruption_type: CorruptionType,
        position: Position,
        ratio: float,
    ) -> CorruptionRecord:
        data = src.read_bytes()
        corrupted = corrupt_bytes(data, corruption_type, position, ratio)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(corrupted)
        return CorruptionRecord(
            original_path=str(src),
            corrupted_path=str(dst),
            corruption_type=corruption_type,
            position=position,
            ratio=ratio,
        )

    def corrupt_sample(
        self,
        sample_dir: Path,
        output_dir: Path,
        corruption_types: list[CorruptionType] | None = None,
        position: Position = 'random',
        ratio_range: tuple[float, float] = (0.1, 0.9),
    ) -> list[CorruptionRecord]:
        if corruption_types is None:
            corruption_types = ['truncate', 'zero_fill', 'random_fill']
        records = []
        for src in sorted(sample_dir.rglob('*')):
            rel = src.relative_to(sample_dir)
            ratio = random.uniform(*ratio_range)
            for ctype in corruption_types:
                dst = output_dir / rel.parent / f"{src.stem}_{ctype}{src.suffix}"
                records.append(self.corrupt_file(src, dst, ctype, position, ratio))
        return records