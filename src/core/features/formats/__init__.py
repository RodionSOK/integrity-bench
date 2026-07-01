from src.core.features.registry import register
from src.core.features.formats.text import TxtChecker, CsvChecker, JsonChecker
from src.core.features.formats.executable import ElfChecker, PeChecker, MachoChecker
from src.core.features.formats.archive import ZipChecker, GzipChecker, SevenZipChecker
from src.core.features.formats.image import PngChecker, JpegChecker, BmpChecker
from src.core.features.formats.video import VideoChecker

register(TxtChecker())
register(CsvChecker())
register(JsonChecker())
register(ElfChecker())
register(PeChecker())
register(MachoChecker())
register(ZipChecker())
register(GzipChecker())
register(SevenZipChecker())
register(PngChecker())
register(JpegChecker())
register(BmpChecker())
register(VideoChecker())
