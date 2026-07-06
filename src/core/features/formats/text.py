import csv
import io
import json

from src.core.features.base import FormatChecker


class TxtChecker(FormatChecker):
    extensions = {'.txt'}

    def check(self, data: bytes) -> dict:
        valid_utf8 = self._check_utf8(data)
        return {'valid_utf8': valid_utf8}

    def _check_utf8(self, data: bytes) -> bool:
        try:
            data.decode('utf-8')
            return True
        except UnicodeDecodeError:
            return False


class CsvChecker(FormatChecker):
    extensions = {'.csv'}

    def check(self, data: bytes) -> dict:
        valid_utf8 = self._check_utf8(data)
        consistent = self._check_consistency(data) if valid_utf8 else False
        return {'valid_utf8': valid_utf8, 'fields_consistent': consistent}

    def _check_utf8(self, data: bytes) -> bool:
        try:
            data.decode('utf-8')
            return True
        except UnicodeDecodeError:
            return False

    def _check_consistency(self, data: bytes) -> bool:
        try:
            text = data.decode('utf-8', errors='replace')
            reader = csv.reader(io.StringIO(text))
            rows = list(reader)
            if not rows:
                return True
            expected = len(rows[0])
            return all(len(row) == expected for row in rows)
        except Exception:
            return False


class JsonChecker(FormatChecker):
    extensions = {'.json'}

    def check(self, data: bytes) -> dict:
        valid_utf8 = self._check_utf8(data)
        valid_json = self._check_json(data) if valid_utf8 else False
        return {'valid_utf8': valid_utf8, 'valid_json': valid_json}

    def _check_utf8(self, data: bytes) -> bool:
        try:
            data.decode('utf-8')
            return True
        except UnicodeDecodeError:
            return False

    def _check_json(self, data: bytes) -> bool:
        try:
            json.loads(data)
            return True
        except Exception:
            return False