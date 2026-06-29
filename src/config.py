from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

ROOT = Path(__file__).parent.parent

SAMPLE_DIR = ROOT / os.getenv('SAMPLE_DIR', 'sample')
CORRUPTED_DIR = ROOT / os.getenv('CORRUPTED_DIR', 'corrupted')
REPORTS_DIR = ROOT / os.getenv('REPORTS_DIR', 'reports')
