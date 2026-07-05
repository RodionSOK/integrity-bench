import json
import struct
import subprocess
from pathlib import Path

from src.core.features.base import FormatChecker

_EBML_MAGIC    = b'\x1a\x45\xdf\xa3'
_SEGMENT_ID    = b'\x18\x53\x80\x67'


class VideoChecker(FormatChecker):
    extensions = {'.mp4', '.mkv', '.avi'}

    def check(self, data: bytes) -> dict:
        raise NotImplementedError("VideoChecker требует путь к файлу, используй check_path()")

    def check_path(self, path: str) -> dict:
        riff_ok = self._check_riff(path)
        if riff_ok is not None and not riff_ok:
            return {'decodable': False, 'riff_size_ok': False}

        ebml_ok = self._check_ebml(path)
        if ebml_ok is not None and not ebml_ok:
            return {'decodable': False, 'ebml_size_ok': False}

        result: dict = {'decodable': self._run_ffprobe(path)}
        if riff_ok is not None:
            result['riff_size_ok'] = True
        if ebml_ok is not None:
            result['ebml_size_ok'] = True
        return result


    def _check_riff(self, path: str) -> bool | None:
        try:
            with open(path, 'rb') as f:
                header = f.read(12)
            if len(header) < 12 or header[:4] != b'RIFF' or header[8:12] != b'AVI ':
                return None
            chunk_size = struct.unpack_from('<I', header, 4)[0]
            return Path(path).stat().st_size >= chunk_size + 8
        except Exception:
            return None


    def _check_ebml(self, path: str) -> bool | None:
        try:
            with open(path, 'rb') as f:
                head = f.read(64)
            if not head.startswith(_EBML_MAGIC):
                return None

            pos = 4
            ebml_size, n = self._read_vint(head, pos)
            if n == 0:
                return None
            pos += n
            if ebml_size is not None:
                pos += ebml_size

            if pos + 4 > len(head) or head[pos:pos + 4] != _SEGMENT_ID:
                return None
            pos += 4

            seg_size, n = self._read_vint(head, pos)
            if n == 0:
                return None
            pos += n

            if seg_size is None:
                return None

            actual = Path(path).stat().st_size
            return actual >= pos + seg_size
        except Exception:
            return None

    @staticmethod
    def _read_vint(data: bytes, pos: int) -> tuple[int | None, int]:
        if pos >= len(data):
            return None, 0
        b = data[pos]
        for width in range(1, 9):
            mask = 0x80 >> (width - 1)
            if b & mask:
                if pos + width > len(data):
                    return None, 0
                value = b ^ mask
                for i in range(1, width):
                    value = (value << 8) | data[pos + i]
                unknown = (1 << (7 * width)) - 1  # все значащие биты = 1
                return (None if value == unknown else value), width
        return None, 0


    def _run_ffprobe(self, path: str) -> bool:
        try:
            proc = subprocess.run(
                ['ffprobe', '-v', 'error',
                 '-show_entries', 'format=duration',
                 '-of', 'json', path],
                capture_output=True,
                timeout=10,
            )
            if proc.returncode != 0:
                return False
            return 'format' in json.loads(proc.stdout)
        except Exception:
            return False