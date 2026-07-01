import gzip
import io
import zipfile
import zlib

from src.core.features.base import FormatChecker

MAGIC_7Z = b'7z\xbc\xaf\x27\x1c'


class ZipChecker(FormatChecker):
    extensions = {'.zip'}

    def check(self, data: bytes) -> dict:
        valid_magic = data[:4] == b'PK\x03\x04'
        crc_ok, decodable = self._check_zip(data) if valid_magic else (False, False)
        return {'valid_magic': valid_magic, 'crc_ok': crc_ok, 'decodable': decodable}

    def _check_zip(self, data: bytes) -> tuple[bool, bool]:
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                for info in zf.infolist():
                    actual = zlib.crc32(zf.read(info.filename)) & 0xFFFFFFFF
                    if actual != info.CRC:
                        return False, True
            return True, True
        except Exception:
            return False, False


class GzipChecker(FormatChecker):
    extensions = {'.gz', '.gzip'}

    def check(self, data: bytes) -> dict:
        valid_magic = data[:2] == b'\x1f\x8b'
        crc_ok, decodable = self._check_gzip(data) if valid_magic else (False, False)
        return {'valid_magic': valid_magic, 'crc_ok': crc_ok, 'decodable': decodable}

    def _check_gzip(self, data: bytes) -> tuple[bool, bool]:
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(data)) as gz:
                content = gz.read()
            stored_crc = int.from_bytes(data[-8:-4], 'little')
            actual_crc = zlib.crc32(content) & 0xFFFFFFFF
            return stored_crc == actual_crc, True
        except Exception:
            return False, False


class SevenZipChecker(FormatChecker):
    extensions = {'.7z'}

    def check(self, data: bytes) -> dict:
        valid_magic = data[:6] == MAGIC_7Z
        return {'valid_magic': valid_magic}
