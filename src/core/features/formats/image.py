import io
import struct
import subprocess
import zlib

from PIL import Image

from src.core.features.base import FormatChecker


class PngChecker(FormatChecker):
    extensions = {'.png'}

    def check(self, data: bytes) -> dict:
        valid_magic = data[:8] == b'\x89PNG\r\n\x1a\n'
        crc_errors, decodable = self._check_png(data) if valid_magic else (0, False)
        return {'valid_magic': valid_magic, 'crc_errors': crc_errors, 'decodable': decodable}

    def _check_png(self, data: bytes) -> tuple[int, bool]:
        errors = 0
        pos = 8
        try:
            while pos + 12 <= len(data):
                length = struct.unpack_from('>I', data, pos)[0]
                chunk_type = data[pos + 4:pos + 8]
                chunk_data = data[pos + 8:pos + 8 + length]
                stored_crc = struct.unpack_from('>I', data, pos + 8 + length)[0]
                actual_crc = zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF
                if stored_crc != actual_crc:
                    errors += 1
                pos += 12 + length
                if chunk_type == b'IEND':
                    break
            decodable = self._decode(data)
        except Exception:
            return errors, False
        return errors, decodable

    def _decode(self, data: bytes) -> bool:
        try:
            Image.open(io.BytesIO(data)).verify()
            return True
        except Exception:
            return False


class JpegChecker(FormatChecker):
    extensions = {'.jpg', '.jpeg'}

    _NO_LENGTH = frozenset({0x01, *range(0xD0, 0xDA)})
    _SOF_CODES = frozenset({
        *range(0xC0, 0xC4), *range(0xC5, 0xC8),
        *range(0xC9, 0xCC), *range(0xCD, 0xD0),
    })

    def check(self, data: bytes) -> dict:
        if len(data) < 4:
            return {
                'valid_soi': False, 'valid_eoi': False, 'decodable': False,
                'has_sof': False, 'has_sos': False, 'markers_ok': False,
            }
        valid_soi = data[:2] == b'\xff\xd8'
        valid_eoi = data[-2:] == b'\xff\xd9'
        decodable = self._decode(data)
        markers = self._scan_markers(data) if valid_soi else {
            'has_sof': False, 'has_sos': False, 'markers_ok': False,
        }
        return {'valid_soi': valid_soi, 'valid_eoi': valid_eoi, 'decodable': decodable, **markers}

    def _scan_markers(self, data: bytes) -> dict:
        has_sof = False
        has_sos = False
        markers_ok = True
        pos = 2

        while pos < len(data):
            while pos < len(data) and data[pos] == 0xFF:
                pos += 1
            if pos >= len(data):
                break

            marker = data[pos]
            pos += 1

            if marker == 0xD9:
                break
            if marker == 0xDA:
                has_sos = True
                break
            if marker in self._NO_LENGTH:
                continue

            if pos + 2 > len(data):
                markers_ok = False
                break
            length = struct.unpack_from('>H', data, pos)[0]
            if length < 2 or pos + length > len(data):
                markers_ok = False
                break

            if marker in self._SOF_CODES:
                has_sof = True

            pos += length

        return {'has_sof': has_sof, 'has_sos': has_sos, 'markers_ok': markers_ok}

    def check_path(self, path: str) -> dict:
        from pathlib import Path
        result = self.check(Path(path).read_bytes())
        result['djpeg_ok'] = self._run_djpeg(path)
        return result

    def _run_djpeg(self, path: str) -> bool:
        try:
            proc = subprocess.run(
                ['djpeg', '-bmp', '-outfile', '/dev/null', path],
                capture_output=True,
                timeout=10,
            )
            return proc.returncode == 0
        except FileNotFoundError:
            return True
        except Exception:
            return True

    def _decode(self, data: bytes) -> bool:
        try:
            img = Image.open(io.BytesIO(data))
            img.load()
            return True
        except Exception:
            return False


class BmpChecker(FormatChecker):
    extensions = {'.bmp'}

    def check(self, data: bytes) -> dict:
        valid_magic = data[:2] == b'BM'
        if not valid_magic:
            return {'valid_magic': False, 'size_ok': False, 'pixel_ok': False, 'decodable': False}
        size_ok = self._check_size(data)
        pixel_ok = self._check_pixel_offset(data)
        decodable = self._decode(data)
        return {'valid_magic': valid_magic, 'size_ok': size_ok, 'pixel_ok': pixel_ok, 'decodable': decodable}

    def _check_size(self, data: bytes) -> bool:
        if len(data) < 6:
            return False
        try:
            bf_size = struct.unpack_from('<I', data, 2)[0]
            return len(data) >= bf_size
        except struct.error:
            return False

    def _check_pixel_offset(self, data: bytes) -> bool:
        if len(data) < 14:
            return False
        try:
            bf_off_bits = struct.unpack_from('<I', data, 10)[0]
            return bf_off_bits < len(data)
        except struct.error:
            return False

    def _decode(self, data: bytes) -> bool:
        try:
            Image.open(io.BytesIO(data)).verify()
            return True
        except Exception:
            return False