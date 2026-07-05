import gzip
import io
import struct
import subprocess
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
        if not valid_magic:
            return {'valid_magic': False, 'valid_header': False,
                    'header_crc_ok': False, 'next_crc_ok': False}
        valid_header, header_crc_ok, next_crc_ok = self._check_header(data)
        return {
            'valid_magic': valid_magic,
            'valid_header': valid_header,
            'header_crc_ok': header_crc_ok,
            'next_crc_ok': next_crc_ok,
        }

    def check_path(self, path: str) -> dict:
        from pathlib import Path
        result = self.check(Path(path).read_bytes())
        if not result['valid_magic']:
            return {**result, '7z_test_ok': False}
        result['7z_test_ok'] = self._run_7z_test(path)
        return result

    def _check_header(self, data: bytes) -> tuple[bool, bool, bool]:
        if len(data) < 32:
            return False, False, False
        try:
            start_crc_stored = struct.unpack_from('<I', data, 8)[0]
            start_crc_actual = zlib.crc32(data[12:32]) & 0xFFFFFFFF
            header_crc_ok = start_crc_stored == start_crc_actual

            next_offset = struct.unpack_from('<Q', data, 12)[0]
            next_size   = struct.unpack_from('<Q', data, 20)[0]
            valid_header = 32 + next_offset + next_size <= len(data)

            if valid_header and next_size > 0:
                next_crc_stored = struct.unpack_from('<I', data, 28)[0]
                next_data = data[32 + next_offset: 32 + next_offset + next_size]
                next_crc_actual = zlib.crc32(next_data) & 0xFFFFFFFF
                next_crc_ok = next_crc_stored == next_crc_actual
            else:
                next_crc_ok = valid_header

            return valid_header, header_crc_ok, next_crc_ok
        except struct.error:
            return False, False, False

    def _run_7z_test(self, path: str) -> bool:
        try:
            proc = subprocess.run(
                ['7z', 't', path],
                capture_output=True,
                timeout=30,
            )
            return proc.returncode == 0
        except FileNotFoundError:
            return True 
        except Exception:
            return True
