# Phils Fusion Tools Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve the complete pre-2.0 state and build the tested, packageable single-add-in foundation that all BOM and Design Tools commands will use.

**Architecture:** A new `Addin/PhilsFusionTools` add-in owns one entry point, command registry, lifecycle, grouped toolbar, and shared services. Existing commands are not installed through this foundation plan; they remain preserved while later plans migrate them behind the tested registry and service interfaces.

**Tech Stack:** Autodesk Fusion CPython add-in API, Python 3.10-compatible pure modules, pytest, Ruff, PowerShell 5.1-compatible backup and packaging scripts, SHA-256 manifests.

## Global Constraints

- Product name is `Phils Fusion Tools`.
- Initial unified version is `2.0.0`.
- Certification target is Windows Autodesk Fusion.
- Install path is `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsFusionTools`.
- Production installation is not changed until a rollback set is created and verified.
- Existing dirty source files and local-only profile files must be preserved.
- Routine commands remain fast; destructive, bulk, overwrite, and structure-changing commands require preflight and confirmation.
- Release packages exclude backups, caches, logs, tests, development notes, build intermediates, and `.superpowers`.
- Source files remain ASCII unless an existing file requires Unicode.
- Every production behaviour change follows red-green-refactor.
- Each commit stages only the files belonging to its task.

---

### Task 1: Capture And Verify The Pre-2.0 Rollback Set

**Files:**
- Create outside repository: `C:/Users/phil9/Documents/PhilsFusionTools-Rollback/<timestamp>/rollback-manifest.json`
- Create outside repository: `C:/Users/phil9/Documents/PhilsFusionTools-Rollback/<timestamp>/restore-phils-fusion-tools.ps1`
- Create outside repository: `C:/Users/phil9/Documents/PhilsFusionTools-Rollback/<timestamp>/verify-rollback.ps1`
- Create outside repository: `C:/Users/phil9/Documents/PhilsFusionTools-Rollback/<timestamp>/source/source.bundle`
- Create outside repository: `C:/Users/phil9/Documents/PhilsFusionTools-Rollback/<timestamp>/source/working-tree.patch`
- Create outside repository: `C:/Users/phil9/Documents/PhilsFusionTools-Rollback/<timestamp>/source/untracked-files.zip`
- Create outside repository: `C:/Users/phil9/Documents/PhilsFusionTools-Rollback/<timestamp>/installed/installed-addins.zip`
- Create outside repository: `C:/Users/phil9/Documents/PhilsFusionTools-Rollback/<timestamp>/settings/settings-and-logs.zip`

**Interfaces:**
- Consumes: Current Git repository, installed add-in folders, BOM settings, and local logs.
- Produces: A timestamped immutable rollback directory whose `rollback-manifest.json` maps every archived relative path to its SHA-256 hash.

- [ ] **Step 1: Record the exact source and installation state**

Run:

```powershell
git -C "C:\Users\phil9\OneDrive\Documents\01-vsc\projects\fusion-360-rules-and-lessons" rev-parse HEAD
git -C "C:\Users\phil9\OneDrive\Documents\01-vsc\projects\fusion-360-rules-and-lessons" status --porcelain=v1
Get-Process | Where-Object { $_.ProcessName -match "Fusion" }
```

Expected: The commit and every dirty path are captured; no backup or installation swap proceeds while Fusion is running.

- [ ] **Step 2: Create the timestamped rollback directory**

Run:

```powershell
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$rollbackRoot = "C:\Users\phil9\Documents\PhilsFusionTools-Rollback\$stamp"
New-Item -ItemType Directory -Force -Path "$rollbackRoot\source","$rollbackRoot\installed","$rollbackRoot\settings","$rollbackRoot\metadata"
```

Expected: All directories are created outside Fusion scan paths.

- [ ] **Step 3: Preserve Git history and tracked modifications**

Run:

```powershell
git -C "C:\Users\phil9\OneDrive\Documents\01-vsc\projects\fusion-360-rules-and-lessons" bundle create "$rollbackRoot\source\source.bundle" --all
git -C "C:\Users\phil9\OneDrive\Documents\01-vsc\projects\fusion-360-rules-and-lessons" diff --binary HEAD | Set-Content -Encoding UTF8 "$rollbackRoot\source\working-tree.patch"
git -C "C:\Users\phil9\OneDrive\Documents\01-vsc\projects\fusion-360-rules-and-lessons" status --porcelain=v1 | Set-Content -Encoding UTF8 "$rollbackRoot\metadata\git-status.txt"
```

Expected: `git bundle verify` succeeds and the binary patch is non-empty.

- [ ] **Step 4: Preserve untracked files without modifying the source tree**

Use PowerShell to resolve each `??` path from `git status --porcelain=v1 -z`, copy it into a temporary mirror beneath the rollback directory, and archive that mirror as `untracked-files.zip`. Store the original relative paths in `metadata/untracked-paths.json`.

Expected: The archive includes the local C Channel, I Beam, and PFC files and every pre-existing backup/build artifact.

- [ ] **Step 5: Archive installed add-ins and settings**

Archive these existing paths when present:

```text
C:\Users\phil9\AppData\Roaming\Autodesk\ApplicationPlugins\PhilsBom.bundle
C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsBom.bundle
C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\MyScripts\Autorun\PhilsBom.bundle
C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsDesignTools
C:\Users\phil9\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\_PhilsDesignTools_Backups
C:\Users\phil9\AppData\Roaming\Autodesk\FusionInstallerBackups
C:\Users\phil9\Documents\PhilsBom
```

Expected: Each source path is represented in the archive inventory, including absent-path status where appropriate.

- [ ] **Step 6: Generate hash manifest and rollback scripts**

`rollback-manifest.json` must contain:

```json
{
  "schema_version": 1,
  "created_at": "ISO-8601 timestamp",
  "source_commit": "40-character commit",
  "source_status_file": "metadata/git-status.txt",
  "archives": [
    {
      "path": "installed/installed-addins.zip",
      "sha256": "64 lowercase hexadecimal characters",
      "source_paths": []
    }
  ]
}
```

`verify-rollback.ps1` recalculates every listed hash and exits non-zero on a mismatch. `restore-phils-fusion-tools.ps1` supports `-DryRun` by default and requires `-Apply` plus a closed Fusion process before replacing scan-path folders.

- [ ] **Step 7: Verify the rollback set**

Run:

```powershell
git bundle verify "$rollbackRoot\source\source.bundle"
powershell -ExecutionPolicy Bypass -File "$rollbackRoot\verify-rollback.ps1"
powershell -ExecutionPolicy Bypass -File "$rollbackRoot\restore-phils-fusion-tools.ps1" -DryRun
```

Expected: All three commands exit `0`; the restore dry-run lists intended destinations without writing them.

- [ ] **Step 8: Record the verified rollback root**

Write the absolute rollback path and manifest hash to:

```text
C:\Users\phil9\Documents\PhilsFusionTools-Rollback\LATEST-VERIFIED.txt
```

Expected: The pointer references the verified timestamped set and is not inside the repository.

---

### Task 2: Create The Isolated 2.0 Worktree And Preserve Intended Local Work

**Files:**
- Modify in isolated worktree: `.gitignore`
- Create in isolated worktree: `docs/migration/pre-2.0-source-inventory.md`
- Apply in isolated worktree: the six tracked local modifications and nine local-only profile files from the verified rollback set.

**Interfaces:**
- Consumes: Verified rollback set from Task 1 and commit `458ea7d` or its verified successor containing only documentation changes.
- Produces: Branch `codex/phils-fusion-tools-2.0` in an isolated worktree with intended local source work preserved in a dedicated baseline commit.

- [ ] **Step 1: Detect existing worktree state**

Run:

```powershell
git -C "C:\Users\phil9\OneDrive\Documents\01-vsc\projects\fusion-360-rules-and-lessons" rev-parse --git-dir
git -C "C:\Users\phil9\OneDrive\Documents\01-vsc\projects\fusion-360-rules-and-lessons" rev-parse --git-common-dir
git -C "C:\Users\phil9\OneDrive\Documents\01-vsc\projects\fusion-360-rules-and-lessons" rev-parse --show-superproject-working-tree
```

Expected: The current checkout is identified as normal or linked before a new worktree is created.

- [ ] **Step 2: Create the isolated worktree**

Use the sibling path:

```text
C:\Users\phil9\OneDrive\Documents\01-vsc\projects\fusion-360-rules-and-lessons-worktrees\phils-fusion-tools-2
```

Run:

```powershell
git -C "C:\Users\phil9\OneDrive\Documents\01-vsc\projects\fusion-360-rules-and-lessons" worktree add "C:\Users\phil9\OneDrive\Documents\01-vsc\projects\fusion-360-rules-and-lessons-worktrees\phils-fusion-tools-2" -b codex/phils-fusion-tools-2.0
```

Expected: The new worktree starts from the committed design and the original dirty checkout remains unchanged.

- [ ] **Step 3: Apply only intended local source work**

Apply the tracked patch only for:

```text
Addin/CHANGELOG.md
Addin/DEVLOG.md
Addin/PhilsDesignTools/PhilsDesignTools.py
Addin/PhilsDesignTools/smg_core.py
Addin/README.md
tasks/todo.md
```

Copy the nine local-only C Channel, I Beam, and PFC Python/icon files from the rollback archive. Do not copy `.bak-*`, `__pycache__`, `*.pyc`, logs, installer `_build`, or historical distribution archives.

- [ ] **Step 4: Expand repository exclusions**

Add these patterns:

```gitignore
.superpowers/
.venv/
__pycache__/
*.py[cod]
*.log
*.bak
*.bak-*
Addin/tools/installer/_build/
Addin/tools/dist/
```

- [ ] **Step 5: Document the preservation boundary**

`docs/migration/pre-2.0-source-inventory.md` records:

- Verified rollback path and manifest hash.
- Original commit and dirty tracked paths.
- Local-only source/assets intentionally carried forward.
- Backup/build artifacts intentionally excluded.
- Installed BOM and Design Tools fingerprints from the audit.

- [ ] **Step 6: Verify and commit the preservation baseline**

Run:

```powershell
py -3.10 -m compileall -q Addin\PhilsDesignTools PhilsBom.bundle\Contents
git diff --check
git status --short
```

Expected: Compilation passes; only intended preservation files and exclusions are staged.

Commit:

```powershell
git add .gitignore Addin/CHANGELOG.md Addin/DEVLOG.md Addin/PhilsDesignTools Addin/README.md tasks/todo.md docs/migration/pre-2.0-source-inventory.md
git commit -m "chore: preserve verified pre-2.0 local source"
```

---

### Task 3: Add The Python Test And Quality Harness

**Files:**
- Create: `pyproject.toml`
- Create: `requirements-dev.txt`
- Create: `tests/conftest.py`
- Create: `tests/test_repository_hygiene.py`
- Create: `tests/test_manifest_contract.py`
- Create: `tools/run_quality.ps1`

**Interfaces:**
- Consumes: Python source and release rules.
- Produces: `pytest`, Ruff, compilation, and repository-hygiene gates runnable without Autodesk Fusion.

- [ ] **Step 1: Write failing quality-configuration and repository-hygiene tests**

```python
from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = ("*.bak", "*.bak-*", "*.pyc", "*.log")


def test_quality_config_targets_python_310():
    config_path = ROOT / "pyproject.toml"
    assert config_path.is_file()
    config = tomllib.loads(config_path.read_text(encoding="utf-8"))
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
```

- [ ] **Step 2: Run the test to verify RED**

Run:

```powershell
py -3.10 -m pytest tests/test_repository_hygiene.py -v
```

Expected: FAIL because `pyproject.toml` does not yet define the quality contract.

- [ ] **Step 3: Configure pytest and Ruff**

`pyproject.toml` must set Python compatibility to `3.10`, test path to `tests`, and Ruff line length to `100`. `requirements-dev.txt` pins compatible major versions of `pytest` and `ruff`.

- [ ] **Step 4: Add the quality runner**

`tools/run_quality.ps1` executes:

```powershell
py -3.10 -m pytest -v
py -3.10 -m ruff check Addin/PhilsFusionTools tests
py -3.10 -m compileall -q Addin/PhilsFusionTools
git diff --check
```

It stops on the first non-zero exit code.

- [ ] **Step 5: Run tests and verify GREEN**

Run:

```powershell
py -3.10 -m pip install -r requirements-dev.txt
powershell -ExecutionPolicy Bypass -File tools/run_quality.ps1
```

Expected: The initial harness passes with the quality configuration present and the release directory absent according to the explicit test contract.

- [ ] **Step 6: Commit**

```powershell
git add pyproject.toml requirements-dev.txt tests tools/run_quality.ps1
git commit -m "test: add unified add-in quality harness"
```

---

### Task 4: Build The Command Registry And Risk Model

**Files:**
- Create: `Addin/PhilsFusionTools/philsfusion/__init__.py`
- Create: `Addin/PhilsFusionTools/philsfusion/registry.py`
- Create: `tests/unit/test_registry.py`

**Interfaces:**
- Produces:
  - `RiskLevel(Enum)`: `ROUTINE`, `BULK`, `DESTRUCTIVE`, `FILE_OVERWRITE`.
  - `CommandSpec(dataclass)`.
  - `CommandRegistry.register(spec: CommandSpec) -> None`.
  - `CommandRegistry.ordered(group: str | None = None) -> tuple[CommandSpec, ...]`.
  - `CommandRegistry.by_id(command_id: str) -> CommandSpec`.

- [ ] **Step 1: Write the failing uniqueness and ordering tests**

```python
import pytest

from philsfusion.registry import CommandRegistry, CommandSpec, RiskLevel


def make_spec(command_id: str, order: int) -> CommandSpec:
    return CommandSpec(
        command_id=command_id,
        name=command_id,
        tooltip="test",
        group="Create",
        order=order,
        resource_key=command_id,
        handler_key=command_id,
        risk=RiskLevel.ROUTINE,
    )


def test_registry_rejects_duplicate_command_ids():
    registry = CommandRegistry()
    registry.register(make_spec("PhilsFusionTools_Test", 1))
    with pytest.raises(ValueError, match="duplicate command id"):
        registry.register(make_spec("PhilsFusionTools_Test", 2))


def test_registry_orders_commands_by_group_order_then_name():
    registry = CommandRegistry()
    registry.register(make_spec("PhilsFusionTools_B", 20))
    registry.register(make_spec("PhilsFusionTools_A", 10))
    assert [item.command_id for item in registry.ordered("Create")] == [
        "PhilsFusionTools_A",
        "PhilsFusionTools_B",
    ]
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```powershell
py -3.10 -m pytest tests/unit/test_registry.py -v
```

Expected: FAIL because `philsfusion.registry` does not exist.

- [ ] **Step 3: Implement the minimal registry**

Use frozen dataclasses and immutable tuple return values. Reject blank IDs, unsupported group names, duplicate visible IDs, duplicate aliases, and aliases equal to the canonical ID.

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```powershell
py -3.10 -m pytest tests/unit/test_registry.py -v
```

Expected: PASS.

- [ ] **Step 5: Add risk-policy tests**

Assert that `ROUTINE` does not require confirmation and the other three risk levels do. Implement `RiskLevel.requires_confirmation`.

- [ ] **Step 6: Commit**

```powershell
git add Addin/PhilsFusionTools/philsfusion tests/unit/test_registry.py
git commit -m "feat: add command registry and risk policy"
```

---

### Task 5: Build Versioned Settings And Atomic File Services

**Files:**
- Create: `Addin/PhilsFusionTools/philsfusion/services/__init__.py`
- Create: `Addin/PhilsFusionTools/philsfusion/services/settings.py`
- Create: `Addin/PhilsFusionTools/philsfusion/services/files.py`
- Create: `tests/unit/test_settings.py`
- Create: `tests/unit/test_files.py`

**Interfaces:**
- Produces:
  - `SettingsStore(path: Path, schema_version: int = 2)`.
  - `SettingsStore.load() -> dict`.
  - `SettingsStore.save(settings: Mapping[str, object]) -> None`.
  - `migrate_bom_settings(raw: Mapping[str, object]) -> dict`.
  - `plan_output_path(target: Path, overwrite: bool) -> OutputPlan`.
  - `atomic_write_bytes(plan: OutputPlan, payload: bytes, validator: Callable[[Path], None]) -> Path`.

- [ ] **Step 1: Write failing settings tests**

```python
import json

from philsfusion.services.settings import SettingsStore


def test_settings_save_is_atomic_and_versioned(tmp_path):
    path = tmp_path / "settings.json"
    store = SettingsStore(path)
    store.save({"ui": {"last_group": "Export"}})
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["schema_version"] == 2
    assert data["ui"]["last_group"] == "Export"
    assert not list(tmp_path.glob("*.tmp"))


def test_corrupt_settings_are_quarantined(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{broken", encoding="utf-8")
    settings = SettingsStore(path).load()
    assert settings["schema_version"] == 2
    assert len(list(tmp_path.glob("settings.corrupt-*.json"))) == 1
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```powershell
py -3.10 -m pytest tests/unit/test_settings.py -v
```

Expected: FAIL because the service does not exist.

- [ ] **Step 3: Implement settings with replace-on-success**

Write JSON to a sibling temporary file, flush and close it, parse it back for validation, then use `os.replace`. Corrupt existing settings are renamed with a UTC timestamp before defaults are returned.

- [ ] **Step 4: Write failing collision and validation tests**

```python
import pytest

from philsfusion.services.files import atomic_write_bytes, plan_output_path


def test_existing_target_requires_explicit_overwrite(tmp_path):
    target = tmp_path / "parts.csv"
    target.write_text("old", encoding="utf-8")
    with pytest.raises(FileExistsError):
        plan_output_path(target, overwrite=False)


def test_validator_failure_preserves_existing_target(tmp_path):
    target = tmp_path / "parts.xml"
    target.write_text("old", encoding="utf-8")
    plan = plan_output_path(target, overwrite=True)
    with pytest.raises(ValueError, match="invalid"):
        atomic_write_bytes(plan, b"<broken", lambda _: (_ for _ in ()).throw(ValueError("invalid")))
    assert target.read_text(encoding="utf-8") == "old"
```

- [ ] **Step 5: Implement atomic output and verify GREEN**

Run:

```powershell
py -3.10 -m pytest tests/unit/test_settings.py tests/unit/test_files.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add Addin/PhilsFusionTools/philsfusion/services tests/unit/test_settings.py tests/unit/test_files.py
git commit -m "feat: add versioned settings and atomic file services"
```

---

### Task 6: Build Preflight, Confirmation, And Result Contracts

**Files:**
- Create: `Addin/PhilsFusionTools/philsfusion/services/safety.py`
- Create: `tests/unit/test_safety.py`

**Interfaces:**
- Produces:
  - `PlannedChange(kind: str, subject: str, summary: str)`.
  - `PreflightPlan(command_id: str, risk: RiskLevel, changes: tuple[PlannedChange, ...], warnings: tuple[str, ...])`.
  - `ExecutionResult(succeeded: tuple[str, ...], skipped: tuple[str, ...], failed: tuple[str, ...], recovery: tuple[str, ...])`.
  - `PreflightPlan.requires_confirmation -> bool`.
  - `ExecutionResult.is_success -> bool`.

- [ ] **Step 1: Write failing result-semantics tests**

```python
from philsfusion.registry import RiskLevel
from philsfusion.services.safety import ExecutionResult, PreflightPlan


def test_result_with_failures_is_not_success():
    result = ExecutionResult(succeeded=("A",), failed=("B: transform restore failed",))
    assert result.is_success is False


def test_destructive_empty_plan_is_invalid():
    plan = PreflightPlan(command_id="Delete", risk=RiskLevel.DESTRUCTIVE)
    assert plan.is_executable is False
    assert plan.requires_confirmation is True
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```powershell
py -3.10 -m pytest tests/unit/test_safety.py -v
```

Expected: FAIL because the safety contracts do not exist.

- [ ] **Step 3: Implement immutable safety contracts**

Defaults use empty tuples, not mutable lists. `is_success` requires at least one success and no failures. `is_executable` requires at least one planned change and no blocking errors.

- [ ] **Step 4: Add deterministic summary tests**

Assert that summaries show risk, change count, warnings, and each planned subject in stable order. Implement `format_preflight(plan)` and `format_result(result)`.

- [ ] **Step 5: Run tests and commit**

```powershell
py -3.10 -m pytest tests/unit/test_safety.py -v
git add Addin/PhilsFusionTools/philsfusion/services/safety.py tests/unit/test_safety.py
git commit -m "feat: add preflight and execution result contracts"
```

---

### Task 7: Build The Single Add-In Lifecycle And Grouped Toolbar

**Files:**
- Create: `Addin/PhilsFusionTools/PhilsFusionTools.manifest`
- Create: `Addin/PhilsFusionTools/PhilsFusionTools.py`
- Create: `Addin/PhilsFusionTools/philsfusion/app.py`
- Create: `Addin/PhilsFusionTools/philsfusion/lifecycle.py`
- Create: `Addin/PhilsFusionTools/philsfusion/catalog.py`
- Create: `Addin/PhilsFusionTools/philsfusion/services/diagnostics.py`
- Create: `tests/unit/test_lifecycle.py`
- Create: `tests/unit/test_diagnostics.py`
- Create: `tests/test_manifest_contract.py`

**Interfaces:**
- Consumes: `CommandRegistry`, service contracts, and an injected Fusion UI adapter.
- Produces:
  - `run(context)` and `stop(context)` in the manifest entry point.
  - `Lifecycle.start() -> None`.
  - `Lifecycle.stop() -> None`.
  - Groups `BOM`, `Create`, `Modify`, `Fabricate`, `Export`, `Cleanup`, and `Help`.
  - `build_diagnostics(...) -> dict`.

- [ ] **Step 1: Write failing lifecycle idempotency tests**

Use a fake adapter that records created and deleted controls, definitions, drop-downs, and handler references.

```python
def test_start_stop_start_does_not_duplicate_controls(fake_ui):
    lifecycle = make_lifecycle(fake_ui)
    lifecycle.start()
    lifecycle.stop()
    lifecycle.start()
    assert fake_ui.visible_control_ids == {
        "PhilsFusionTools_BOM",
        "PhilsFusionTools_Create",
        "PhilsFusionTools_Modify",
        "PhilsFusionTools_Fabricate",
        "PhilsFusionTools_Export",
        "PhilsFusionTools_Cleanup",
        "PhilsFusionTools_Help",
    }
    assert fake_ui.retained_handler_count == fake_ui.expected_handler_count
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```powershell
py -3.10 -m pytest tests/unit/test_lifecycle.py -v
```

Expected: FAIL because the lifecycle does not exist.

- [ ] **Step 3: Add the manifest contract test**

The test reads the JSON manifest and asserts:

```python
assert manifest["id"] == "PhilsFusionTools"
assert manifest["version"] == "2.0.0"
assert manifest["runOnStartup"] is True
assert manifest["supportedOS"] == "windows"
assert manifest["engine"] == "CPython"
assert manifest["entry"] == "PhilsFusionTools.py"
```

- [ ] **Step 4: Implement the entry point and lifecycle**

The entry point prepends its directory to `sys.path`, imports only the uniquely named `philsfusion` package, and delegates to one app instance. It never imports generic `smg_*` modules by global name.

The lifecycle owns every created control, command definition, event handler, and toolbar group and releases each in reverse order on stop.

- [ ] **Step 5: Add the approved shell catalog**

Register visible shell controls in this order:

```text
BOM
Create
Modify
Fabricate
Export
Cleanup
Help
```

Only Help has an executable diagnostic command during this foundation phase. Empty migration groups remain explicitly marked as unavailable in development builds and are not packaged as a production release.

- [ ] **Step 6: Implement diagnostics**

Diagnostics returns version, source commit, package fingerprint, install path, settings schema, startup health, migration status, and log path. It never includes document names, geometry, selections, or exported data.

- [ ] **Step 7: Run tests and compile**

Run:

```powershell
py -3.10 -m pytest tests/unit/test_lifecycle.py tests/unit/test_diagnostics.py tests/test_manifest_contract.py -v
py -3.10 -m compileall -q Addin\PhilsFusionTools
```

Expected: PASS.

- [ ] **Step 8: Commit**

```powershell
git add Addin/PhilsFusionTools tests/unit/test_lifecycle.py tests/unit/test_diagnostics.py tests/test_manifest_contract.py
git commit -m "feat: add unified add-in lifecycle and grouped toolbar"
```

---

### Task 8: Build The Clean Foundation Package And Gate The Next Phase

**Files:**
- Create: `tools/package_phils_fusion_tools.ps1`
- Create: `release/package-allowlist.txt`
- Modify: `tests/conftest.py`
- Create: `tests/test_package_contents.py`
- Create: `docs/verification/foundation-verification.md`

**Interfaces:**
- Consumes: Clean committed `Addin/PhilsFusionTools` source.
- Produces: A non-production foundation ZIP containing only allow-listed files and a SHA-256 manifest.

- [ ] **Step 1: Write the failing package-content test**

```python
from pathlib import Path
import zipfile
import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def foundation_package():
    packages = sorted((ROOT / "build").glob("PhilsFusionTools-2.0.0-foundation.zip"))
    assert len(packages) == 1
    return packages[0]


def test_package_contains_only_runtime_files(foundation_package):
    with zipfile.ZipFile(foundation_package) as archive:
        names = archive.namelist()
    assert all("/tests/" not in f"/{name}" for name in names)
    assert all("__pycache__" not in name for name in names)
    assert all(".bak-" not in name for name in names)
    assert all(not name.endswith((".pyc", ".log")) for name in names)
    assert "PhilsFusionTools/PhilsFusionTools.manifest" in names
    assert "PhilsFusionTools/PhilsFusionTools.py" in names
```

- [ ] **Step 2: Run the test to verify RED**

Run:

```powershell
py -3.10 -m pytest tests/test_package_contents.py -v
```

Expected: FAIL because the package fixture or builder does not exist.

- [ ] **Step 3: Implement the allow-list packager**

The packager:

- Requires a clean index for unified add-in paths.
- Copies only the manifest, entry point, `philsfusion/**/*.py`, and `resources/**/*`.
- Excludes `__pycache__`, `*.pyc`, `*.log`, `.bak*`, tests, and development files.
- Writes `build-info.json` containing version, commit, UTC timestamp, and package tree hash.
- Produces `PhilsFusionTools-2.0.0-foundation.zip` and its `.sha256` file.
- Labels the artifact `foundation` and refuses an install action.

- [ ] **Step 4: Run the package test to verify GREEN**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File tools/package_phils_fusion_tools.ps1 -Foundation
py -3.10 -m pytest tests/test_package_contents.py -v
```

Expected: PASS.

- [ ] **Step 5: Run the complete foundation quality gate**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File tools/run_quality.ps1
git status --short
```

Expected: All tests, Ruff, compilation, and diff checks pass. Only explicitly ignored build output may be untracked.

- [ ] **Step 6: Record evidence**

`docs/verification/foundation-verification.md` records:

- Verified rollback root and manifest hash.
- Worktree path and commit.
- Python, pytest, and Ruff versions.
- Test counts and result.
- Compilation result.
- Package filename, SHA-256, file count, and allow-list result.
- Confirmation that no Fusion scan-path installation changed.

- [ ] **Step 7: Commit**

```powershell
git add tools/package_phils_fusion_tools.ps1 release/package-allowlist.txt tests/test_package_contents.py docs/verification/foundation-verification.md
git commit -m "build: add clean foundation packaging gate"
```

- [ ] **Step 8: Review gate**

Do not install the foundation package. Review the complete diff and verification evidence before creating the BOM migration plan.

Expected: The foundation is testable and packageable, while the current working Fusion installation remains exactly recoverable from the verified rollback set.
