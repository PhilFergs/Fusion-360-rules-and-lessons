import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "Addin" / "PhilsFusionTools" / "PhilsFusionTools.manifest"


def test_manifest_declares_one_windows_cpython_addin():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert manifest["autodeskProduct"] == "fusion360"
    assert manifest["type"] == "addin"
    assert manifest["id"] == "PhilsFusionTools"
    assert manifest["version"] == "2.0.0"
    assert manifest["runOnStartup"] is True
    assert manifest["supportedOS"] == "windows"
    assert manifest["engine"] == "CPython"
    assert manifest["entry"] == "PhilsFusionTools.py"
