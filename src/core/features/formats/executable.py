import struct

from src.core.features.base import FormatChecker

MAGIC_ELF = b'\x7fELF'
MAGIC_PE = b'MZ'
MAGIC_MACHO = {
    b'\xfe\xed\xfa\xce',
    b'\xfe\xed\xfa\xcf',
    b'\xce\xfa\xed\xfe',
    b'\xcf\xfa\xed\xfe',
}


class ElfChecker(FormatChecker):
    extensions = {'.elf', '.so'}

    def check(self, data: bytes) -> dict:
        valid_magic = data[:4] == MAGIC_ELF
        valid_header = self._check_header(data) if valid_magic else False
        return {'valid_magic': valid_magic, 'valid_header': valid_header}

    def _check_header(self, data: bytes) -> bool:
        if len(data) < 64:
            return False
        try:
            e_shoff = struct.unpack_from('<Q', data, 40)[0]
            e_shnum = struct.unpack_from('<H', data, 60)[0]
            e_shentsize = struct.unpack_from('<H', data, 58)[0]
            if e_shoff == 0:
                return True
            return e_shoff + e_shnum * e_shentsize <= len(data)
        except struct.error:
            return False


class PeChecker(FormatChecker):
    extensions = {'.exe', '.dll'}

    def check(self, data: bytes) -> dict:
        valid_magic = data[:2] == MAGIC_PE
        valid_header = self._check_header(data) if valid_magic else False
        return {'valid_magic': valid_magic, 'valid_header': valid_header}

    def _check_header(self, data: bytes) -> bool:
        if len(data) < 64:
            return False
        try:
            pe_offset = struct.unpack_from('<I', data, 60)[0]
            if pe_offset + 4 > len(data):
                return False
            return data[pe_offset:pe_offset + 4] == b'PE\x00\x00'
        except struct.error:
            return False


class MachoChecker(FormatChecker):
    extensions = {'.macho', ''}

    def check(self, data: bytes) -> dict:
        valid_magic = data[:4] in MAGIC_MACHO
        valid_header = self._check_header(data) if valid_magic else False
        return {'valid_magic': valid_magic, 'valid_header': valid_header}

    def _check_header(self, data: bytes) -> bool:
        if len(data) < 28:
            return False
        try:
            magic = data[:4]
            little = magic in {b'\xce\xfa\xed\xfe', b'\xcf\xfa\xed\xfe'}
            fmt = '<I' if little else '>I'
            ncmds = struct.unpack_from(fmt, data, 16)[0]
            sizeofcmds = struct.unpack_from(fmt, data, 20)[0]
            header_size = 28 if magic in {b'\xce\xfa\xed\xfe', b'\xfe\xed\xfa\xce'} else 32
            return header_size + sizeofcmds <= len(data) and ncmds < 256
        except struct.error:
            return False