import io
import struct
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

    def check(self, data: bytes) -> dict:
        valid_soi = data[:2] == b'\xff\xd8'
        valid_eoi = data[-2:] == b'\xff\xd9'
        decodable = self._decode(data)
        return {'valid_soi': valid_soi, 'valid_eoi': valid_eoi, 'decodable': decodable}

    def _decode(self, data: bytes) -> bool:
        try:
            Image.open(io.BytesIO(data)).verify()
            return True
        except Exception:
            return False


class BmpChecker(FormatChecker):
    extensions = {'.bmp'}

    def check(self, data: bytes) -> dict:
        valid_magic = data[:2] == b'BM'
        size_ok = self._check_size(data) if valid_magic else False
        decodable = self._decode(data) if valid_magic else False
        return {'valid_magic': valid_magic, 'size_ok': size_ok, 'decodable': decodable}

    def _check_size(self, data: bytes) -> bool:
        try:
            bf_size = struct.unpack_from('<I', data, 2)[0]
            return bf_size == len(data)
        except struct.error:
            return False

    def _decode(self, data: bytes) -> bool:
        try:
            Image.open(io.BytesIO(data)).verify()
            return True
        except Exception:
            return False