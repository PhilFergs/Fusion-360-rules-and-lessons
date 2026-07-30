from pathlib import Path

import tomli

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = ("*.bak", "*.bak-*", "*.pyc", "*.log")


def test_quality_config_targets_python_310():
    config_path = ROOT / "pyproject.toml"
    assert config_path.is_file()
    config = tomli.loads(config_path.read_text(encoding="utf-8"))
    assert config["tool"]["ruff"]["target-version"] == "py310"
    assert config["tool"]["pytest"]["ini_options"]["testpaths"] == ["tests"]


def test_unified_release_tree_contains_no_forbidden_files():
    release_root = ROOT / "Addin" / "PhilsFusionTools"
    if not release_root.exists():
        return

    offenders = sorted(
        path.relative_to(ROOT).as_posix()
        for pattern in FORBIDDEN
        for path in release_root.rglob(pattern)
    )
    assert offenders == []
