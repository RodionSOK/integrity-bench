from dataclasses import dataclass, field
from typing import Callable

from src.core.features.formats.archive import GzipChecker, ZipChecker
from src.core.features.formats.executable import ElfChecker, PeChecker
from src.core.features.formats.image import BmpChecker, JpegChecker, PngChecker
from src.core.features.formats.video import VideoChecker

_zip   = ZipChecker()
_gzip  = GzipChecker()
_png   = PngChecker()
_jpeg  = JpegChecker()
_bmp   = BmpChecker()
_elf   = ElfChecker()
_pe    = PeChecker()
_video = VideoChecker()


@dataclass
class CrcSpec:
    checker: object                  
    ok_fn: Callable[[dict], bool]   


@dataclass
class StructuralSpec:
    checker: object                  
    ok_fn: Callable[[dict], bool]    
    confidence: float
    needs_path: bool = False         


@dataclass
class StatSpec:
    v_low: float                     
    v_high: float                    


@dataclass
class FormatSpec:
    crc:        CrcSpec        | None = None
    structural: StructuralSpec | None = None
    statistical: StatSpec      | None = None

HINT_TO_EXT: dict[str, str] = {
    'txt': '.txt', 'csv': '.csv', 'json': '.json',
    'elf': '.so',  'pe': '.exe',  'macho': '',
    'zip': '.zip', 'gzip': '.gz', '7z': '.7z',
    'png': '.png', 'jpeg': '.jpg', 'bmp': '.bmp',
    'mp4': '.mp4', 'mkv': '.mkv', 'avi': '.avi',
}
EXT_TO_HINT: dict[str, str] = {v: k for k, v in HINT_TO_EXT.items()}


FORMAT_SPECS: dict[str, FormatSpec] = {

    'txt':  FormatSpec(statistical=StatSpec(0.000, 0.111)),
    'csv':  FormatSpec(statistical=StatSpec(0.000, 3.851)), 
    'json': FormatSpec(statistical=StatSpec(0.000, 0.199)),

    'zip': FormatSpec(
        crc=CrcSpec(
            checker=_zip,
            ok_fn=lambda s: bool(s.get('crc_ok')) and bool(s.get('decodable')),
        ),
        statistical=StatSpec(0.000, 0.024),
    ),
    'gzip': FormatSpec(
        crc=CrcSpec(
            checker=_gzip,
            ok_fn=lambda s: bool(s.get('crc_ok')) and bool(s.get('decodable')),
        ),
        statistical=StatSpec(0.003, 0.007),
    ),
    '7z': FormatSpec(statistical=StatSpec(0.000, 0.020)),

    'png': FormatSpec(
        crc=CrcSpec(
            checker=_png,
            ok_fn=lambda s: s.get('crc_errors', 1) == 0 and bool(s.get('decodable')),
        ),
        statistical=StatSpec(0.000, 1.138),
    ),
    'jpeg': FormatSpec(
        structural=StructuralSpec(
            checker=_jpeg,
            ok_fn=lambda s: (bool(s.get('valid_soi'))
                             and bool(s.get('valid_eoi'))
                             and bool(s.get('decodable'))),
            confidence=0.6,
        ),
        statistical=StatSpec(0.000, 4.140), 
    ),
    'bmp': FormatSpec(
        structural=StructuralSpec(
            checker=_bmp,
            ok_fn=lambda s: bool(s.get('size_ok')),
            confidence=0.35,
        ),
        statistical=StatSpec(0.000, 1.293),
    ),

    'elf': FormatSpec(
        structural=StructuralSpec(
            checker=_elf,
            ok_fn=lambda s: bool(s.get('valid_magic')) and bool(s.get('valid_header')),
            confidence=0.5,
        ),
        statistical=StatSpec(1.298, 6.230),
    ),
    'pe': FormatSpec(
        structural=StructuralSpec(
            checker=_pe,
            ok_fn=lambda s: bool(s.get('valid_magic')) and bool(s.get('valid_header')),
            confidence=0.2,
        ),
        statistical=StatSpec(0.000, 2.486),  # ! CV=130%
    ),
    'macho': FormatSpec(statistical=StatSpec(3.618, 5.711)),

    'mp4': FormatSpec(
        structural=StructuralSpec(
            checker=_video,
            ok_fn=lambda s: bool(s.get('decodable')),
            confidence=0.5,
            needs_path=True,
        ),
        statistical=StatSpec(0.000, 0.377),
    ),
    'mkv': FormatSpec(
        structural=StructuralSpec(
            checker=_video,
            ok_fn=lambda s: bool(s.get('decodable')),
            confidence=0.5,
            needs_path=True,
        ),
        statistical=StatSpec(0.008, 0.018),
    ),
    'avi': FormatSpec(
        structural=StructuralSpec(
            checker=_video,
            ok_fn=lambda s: bool(s.get('decodable')),
            confidence=0.5,
            needs_path=True,
        ),
        statistical=StatSpec(0.871, 2.578),
    ),
}
