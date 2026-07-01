import json
import subprocess

from src.core.features.base import FormatChecker


class VideoChecker(FormatChecker):
    extensions = {'.mp4', '.mkv', '.avi'}

    def check(self, data: bytes) -> dict:
        raise NotImplementedError("VideoChecker требует путь к файлу, используй check_path()")

    def check_path(self, path: str) -> dict:
        result = self._run_ffprobe(path)
        return {'decodable': result}

    def _run_ffprobe(self, path: str) -> bool:
        try:
            proc = subprocess.run(
                [
                    'ffprobe', '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-of', 'json', path,
                ],
                capture_output=True,
                timeout=10,
            )
            if proc.returncode != 0:
                return False
            info = json.loads(proc.stdout)
            return 'format' in info
        except Exception:
            return False