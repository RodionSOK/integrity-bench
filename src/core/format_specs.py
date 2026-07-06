from dataclasses import dataclass
from typing import Callable

from src.core.features.formats.archive import GzipChecker, SevenZipChecker, ZipChecker
from src.core.features.formats.executable import ElfChecker, PeChecker
from src.core.features.formats.image import BmpChecker, JpegChecker, PngChecker
from src.core.features.formats.video import VideoChecker

_zip   = ZipChecker()
_gzip  = GzipChecker()
_7z    = SevenZipChecker()
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
    ml_group:   str            | None = None

HINT_TO_EXT: dict[str, str] = {
    'txt': '.txt', 'csv': '.csv', 'json': '.json',
    'elf': '.so',  'pe': '.exe',  'macho': '',
    'zip': '.zip', 'gzip': '.gz', '7z': '.7z',
    'png': '.png', 'jpeg': '.jpg', 'bmp': '.bmp',
    'mp4': '.mp4', 'mkv': '.mkv', 'avi': '.avi',
}
EXT_TO_HINT: dict[str, str] = {v: k for k, v in HINT_TO_EXT.items()}


FORMAT_SPECS: dict[str, FormatSpec] = {

    'txt':  FormatSpec(statistical=StatSpec(0.000, 2.030), ml_group='text'),
    'csv':  FormatSpec(statistical=StatSpec(0.000, 4.840), ml_group='text'),
    'json': FormatSpec(statistical=StatSpec(0.000, 1.171), ml_group='text'),

    'zip': FormatSpec(
        crc=CrcSpec(
            checker=_zip,
            ok_fn=lambda s: bool(s.get('crc_ok')) and bool(s.get('decodable')),
        ),
        statistical=StatSpec(0.000, 0.025),
    ),
    'gzip': FormatSpec(
        crc=CrcSpec(
            checker=_gzip,
            ok_fn=lambda s: bool(s.get('crc_ok')) and bool(s.get('decodable')),
        ),
        statistical=StatSpec(0.003, 0.007),
    ),
    '7z': FormatSpec(
        structural=StructuralSpec(
            checker=_7z,
            ok_fn=lambda s: (
                bool(s.get('valid_magic'))
                and bool(s.get('valid_header'))
                and bool(s.get('header_crc_ok', True))
                and bool(s.get('next_crc_ok', True))
                and bool(s.get('7z_test_ok', True))
            ),
            confidence=0.9,
            needs_path=True,
        ),
        statistical=StatSpec(0.000, 0.043),
    ),

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
                             and bool(s.get('decodable'))
                             and bool(s.get('has_sof'))
                             and bool(s.get('has_sos'))
                             and bool(s.get('markers_ok'))
                             and bool(s.get('djpeg_ok', True))),
            confidence=0.6,
            needs_path=True,
        ),
        statistical=StatSpec(0.000, 9.355),
        ml_group='image_nc',
    ),
    'bmp': FormatSpec(
        structural=StructuralSpec(
            checker=_bmp,
            ok_fn=lambda s: bool(s.get('size_ok')) and bool(s.get('pixel_ok')),
            confidence=0.5,
        ),
        statistical=StatSpec(0.000, 8.410),
        ml_group='image_nc',
    ),

    'elf': FormatSpec(
        structural=StructuralSpec(
            checker=_elf,
            ok_fn=lambda s: bool(s.get('valid_magic')) and bool(s.get('valid_header')),
            confidence=0.5,
        ),
        statistical=StatSpec(1.118, 5.074),
        ml_group='executable',
    ),
    'pe': FormatSpec(
        structural=StructuralSpec(
            checker=_pe,
            ok_fn=lambda s: not bool(s.get('valid_pe_sig')) or bool(s.get('sections_fit')),
            confidence=0.5,
        ),
        statistical=StatSpec(0.000, 9.677),
        ml_group='executable',
    ),
    'macho': FormatSpec(statistical=StatSpec(2.127, 6.643), ml_group='executable'),

    'mp4': FormatSpec(
        structural=StructuralSpec(
            checker=_video,
            ok_fn=lambda s: bool(s.get('decodable')),
            confidence=0.5,
            needs_path=True,
        ),
        statistical=StatSpec(0.000, 0.485),
        ml_group='video',
    ),
    'mkv': FormatSpec(
        structural=StructuralSpec(
            checker=_video,
            ok_fn=lambda s: bool(s.get('decodable')) and s.get('ebml_size_ok', True),
            confidence=0.5,
            needs_path=True,
        ),
        statistical=StatSpec(0.000, 0.065),
        ml_group='video',
    ),
    'avi': FormatSpec(
        structural=StructuralSpec(
            checker=_video,
            ok_fn=lambda s: bool(s.get('decodable')) and s.get('riff_size_ok', True),
            confidence=0.5,
            needs_path=True,
        ),
        statistical=StatSpec(0.000, 4.511),
        ml_group='video',
    ),
}
