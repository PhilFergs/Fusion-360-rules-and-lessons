import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADDIN_ROOT = ROOT / "Addin" / "PhilsFusionTools"

if ADDIN_ROOT.is_dir():
    sys.path.insert(0, str(ADDIN_ROOT))
