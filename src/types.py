from typing import Literal

CorruptionType = Literal['truncate', 'zero_fill', 'random_fill']
Position = Literal['start', 'middle', 'end', 'random']