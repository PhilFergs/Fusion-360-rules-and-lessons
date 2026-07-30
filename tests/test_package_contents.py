import hashlib
import json
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_PATH = ROOT / "build" / "PhilsFusionTools-2.0.0.zip"
HASH_PATH = PACKAGE_PATH.with_suffix(PACKAGE_PATH.suffix + ".sha256")


@pytest.fixture
def production_package():
    assert PACKAGE_PATH.is_file(), "run tools/package_phils_fusion_tools.ps1 -Production"
    return PACKAGE_PATH


def test_package_contains_only_runtime_files(production_package):
    with zipfile.ZipFile(production_package) as archive:
        names = archive.namelist()

    assert all("/tests/" not in f"/{name}" for name in names)
    assert all("__pycache__" not in name for name in names)
    assert all(".bak" not in name.casefold() for name in names)
    assert all(not name.endswith((".pyc", ".log")) for name in names)
    assert "PhilsFusionTools/PhilsFusionTools.manifest" in names
    assert "PhilsFusionTools/PhilsFusionTools.py" in names
    assert "PhilsFusionTools/build-info.json" in names


def test_package_matches_allowlist_and_embeds_build_identity(production_package):
    allowlist = {
        line.strip()
        for line in (ROOT / "release" / "package-allowlist.txt").read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    with zipfile.ZipFile(production_package) as archive:
        names = set(archive.namelist())
        build_info = json.loads(
            archive.read("PhilsFusionTools/build-info.json").decode("utf-8")
        )

    assert names == allowlist
    assert build_info["version"] == "2.0.0"
    assert build_info["artifact"] == "production"
    assert len(build_info["commit"]) == 40
    assert len(build_info["package_tree_hash"]) == 64


def test_package_sidecar_hash_matches_archive(production_package):
    expected_hash = HASH_PATH.read_text(encoding="ascii").split()[0]
    actual_hash = hashlib.sha256(production_package.read_bytes()).hexdigest()

    assert expected_hash == actual_hash


def test_production_package_has_no_legacy_roots(production_package):
    with zipfile.ZipFile(production_package) as archive:
        names = archive.namelist()

    assert not any(name.startswith("PhilsDesignTools/") for name in names)
    assert not any(name.startswith("PhilsBom.bundle/") for name in names)


def test_every_top_level_icon_folder_has_valid_svg_sizes():
    from xml.etree import ElementTree

    resource_root = ROOT / "Addin" / "PhilsFusionTools" / "resources"
    expected = {
        "bom",
        "create",
        "modify",
        "fabricate",
        "export",
        "cleanup",
        "help",
        "diagnostics",
        "about-migration",
    }

    assert {path.name for path in resource_root.iterdir() if path.is_dir()} == expected
    for folder in resource_root.iterdir():
        if not folder.is_dir():
            continue
        for name in ("16x16.svg", "32x32.svg"):
            icon = folder / name
            assert icon.is_file(), icon
            assert ElementTree.parse(icon).getroot().tag.endswith("svg")
