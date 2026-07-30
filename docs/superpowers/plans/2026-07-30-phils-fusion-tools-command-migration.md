# Phils Fusion Tools Command Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate every supported Phils BOM and Phils Design Tools command into one tested, grouped, rollback-safe Windows Fusion add-in and retire the duplicate legacy installations only after a verified startup health check.

**Architecture:** Pure catalog, safety, settings, naming, and export code remains independent of Autodesk's runtime and is tested with pytest. Fusion-specific command actions bind canonical and hidden compatibility definitions to the same handlers, while one lifecycle owns all controls, definitions, context-menu hooks, and handler references. The six duplicate profile commands become one data-driven Steel Member command backed by the preserved geometry engine.

**Tech Stack:** Python 3.10, Autodesk Fusion CPython API, pytest 8.4, Ruff 0.12, PowerShell 5.1, JSON, plist migration, ZIP/XLSX standard-library writers.

## Global Constraints

- Product name: `Phils Fusion Tools`.
- Version: `2.0.0`.
- Platform: Windows only.
- Fusion install target: `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\PhilsFusionTools`.
- Public groups, in order: BOM, Create, Modify, Fabricate, Export, Cleanup, Help.
- Prompt policy: routine actions use their normal command dialog; bulk, destructive, and overwrite actions require an additional preflight confirmation.
- Compatibility policy: hidden legacy IDs remain for the 2.x transition and never add toolbar controls.
- Settings and logs live under `%USERPROFILE%\Documents\PhilsFusionTools`, never beside installed Python.
- Every output is written to a validated temporary sibling and promoted with `os.replace`.
- No source, installed add-in, or legacy archive is deleted without the verified rollback package.
- Fusion must be closed for installation, quarantine, final archive, or rollback.
- Use Autodesk's documented command handlers directly; never call `CommandDefinition.execute` from a command event.
- All manual code edits use `apply_patch`; mechanical namespace copies and formatter-driven bulk edits may use scripted transformations.

---

### Task 1: Lock The Production Command Catalog

**Files:**
- Create: `Addin/PhilsFusionTools/philsfusion/commands/__init__.py`
- Create: `Addin/PhilsFusionTools/philsfusion/commands/specs.py`
- Modify: `Addin/PhilsFusionTools/philsfusion/catalog.py`
- Create: `tests/unit/test_command_catalog.py`

**Interfaces:**
- Consumes: `CommandRegistry`, `CommandSpec`, `RiskLevel`, and the command matrix in `docs/migration/legacy-command-audit.md`.
- Produces: `build_command_registry() -> CommandRegistry`, `PUBLIC_COMMAND_IDS`, `LEGACY_ALIAS_IDS`, and `PROFILE_LEGACY_IDS`.

- [ ] **Step 1: Write the failing catalog coverage test**

```python
def test_production_catalog_has_all_groups_and_no_visible_legacy_ids():
    registry = build_command_registry()
    specs = registry.ordered()

    assert len(specs) == 25
    assert {spec.group for spec in specs} == set(GROUP_ORDER)
    assert all(spec.command_id.startswith("PhilsFusionTools_") for spec in specs)
    assert not set(PUBLIC_COMMAND_IDS) & set(LEGACY_ALIAS_IDS)
    assert set(PROFILE_LEGACY_IDS) == {
        "PhilsDesignTools_EA",
        "PhilsDesignTools_SHS",
        "PhilsDesignTools_RHS",
        "PhilsDesignTools_IBeam",
        "PhilsDesignTools_PFC",
        "PhilsDesignTools_CChannel",
    }
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_command_catalog.py -v
```

Expected: import failure because `philsfusion.commands.specs` does not exist.

- [ ] **Step 3: Define all 25 canonical specs**

Use the exact group, order, risk, handler key, resource key, and aliases from the
audit matrix. Assign `RiskLevel.ROUTINE` only to BOM Settings, Create Steel
Member, Diagnostics, and About/Migration. Assign `FILE_OVERWRITE` to all five
exports including Create BOM. Assign `DESTRUCTIVE` to Split Body, Delete Split
Bodies, Bulk Replace Components, Hole Cut, and Normalize Structure. Assign
`BULK` to the remaining design commands.

- [ ] **Step 4: Replace the foundation registry**

Change `catalog.py` so `build_foundation_registry` becomes
`build_command_registry`. Keep `SHELL_GROUPS`, mark every group available, and
export the production registry from `commands/specs.py`.

- [ ] **Step 5: Run tests and commit**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_command_catalog.py tests\unit\test_registry.py -v
git add Addin/PhilsFusionTools/philsfusion/commands Addin/PhilsFusionTools/philsfusion/catalog.py tests/unit/test_command_catalog.py
git commit -m "feat: define the production command catalog"
```

---

### Task 2: Generalize Lifecycle-Owned Command Actions

**Files:**
- Create: `Addin/PhilsFusionTools/philsfusion/fusion/__init__.py`
- Create: `Addin/PhilsFusionTools/philsfusion/fusion/actions.py`
- Modify: `Addin/PhilsFusionTools/philsfusion/lifecycle.py`
- Modify: `Addin/PhilsFusionTools/philsfusion/app.py`
- Modify: `tests/unit/test_lifecycle.py`
- Create: `tests/unit/test_command_actions.py`

**Interfaces:**
- Consumes: `CommandSpec` and the existing `UiRegistration` lifecycle contract.
- Produces:
  - `InstalledCommand(owned_objects: tuple, handler_refs: tuple)`.
  - `CommandAction.install(ui, controls, spec) -> InstalledCommand`.
  - `SimpleCommandAction(callback)`.
  - `ModuleCommandAction(module_name, created_handler_name, legacy_bindings=())`.

- [ ] **Step 1: Write failing action ownership tests**

```python
def test_module_action_installs_one_visible_and_hidden_compatibility_definitions(fake_fusion):
    action = ModuleCommandAction(
        "philsfusion.commands.design.rotate",
        "RotateCreatedHandler",
        legacy_bindings=("PhilsDesignTools_Rotate",),
    )

    installed = action.install(fake_fusion.ui, fake_fusion.controls, ROTATE_SPEC)

    assert fake_fusion.visible_ids == {"PhilsFusionTools_RotateSteelMember"}
    assert fake_fusion.definition_ids == {
        "PhilsFusionTools_RotateSteelMember",
        "PhilsDesignTools_Rotate",
    }
    assert len(installed.handler_refs) == 2
```

- [ ] **Step 2: Run and verify RED**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_command_actions.py -v
```

Expected: `philsfusion.fusion.actions` import failure.

- [ ] **Step 3: Implement command action installation**

`ModuleCommandAction` imports only its fully qualified package name. It creates a
canonical button definition and control, then creates hidden definitions for
each legacy binding. Each definition receives a fresh instance of the same
command-created handler. It returns every definition, visible control, and
handler reference to the lifecycle registration.

- [ ] **Step 4: Update the Fusion adapter**

Replace direct callback wrapping in `FusionUiAdapter.register_group` with:

```python
installed = action.install(self._ui, group_control.controls, spec)
owned.extend(installed.owned_objects)
handlers.extend(installed.handler_refs)
```

Retain `SimpleCommandAction` for Diagnostics and About/Migration. If one command
fails during group registration, dispose all objects created by that group and
let `Lifecycle.start` roll back prior groups.

- [ ] **Step 5: Run lifecycle and action tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_lifecycle.py tests\unit\test_command_actions.py -v
```

- [ ] **Step 6: Commit**

```powershell
git add Addin/PhilsFusionTools/philsfusion/fusion Addin/PhilsFusionTools/philsfusion/lifecycle.py Addin/PhilsFusionTools/philsfusion/app.py tests/unit/test_lifecycle.py tests/unit/test_command_actions.py
git commit -m "refactor: make lifecycle own command actions"
```

---

### Task 3: Namespace And Harden The Preserved Design Engine

**Files:**
- Create: `Addin/PhilsFusionTools/philsfusion/commands/design/__init__.py`
- Create: `Addin/PhilsFusionTools/philsfusion/commands/design/context.py`
- Create: `Addin/PhilsFusionTools/philsfusion/commands/design/core.py`
- Create: `Addin/PhilsFusionTools/philsfusion/commands/design/logger.py`
- Create: `Addin/PhilsFusionTools/philsfusion/commands/design/*.py` for the 18 non-profile command modules
- Create: `Addin/PhilsFusionTools/philsfusion/commands/design/resources/**`
- Create: `tests/unit/test_design_namespace.py`
- Create: `tests/unit/test_design_logger.py`

**Interfaces:**
- Consumes: the preserved `smg_*` files and resources recorded in `pre-2.0-source-inventory.md`.
- Produces:
  - `context.init(app, ui)`, `context.add_handler(handler)`,
    `context.clear_handlers()`, `context.handler_count()`.
  - `logger.configure(log_path: Path)`, `logger.log(message)`.
  - Fully qualified imports under `philsfusion.commands.design`.

- [ ] **Step 1: Write failing namespace and logger tests**

```python
def test_design_modules_never_import_global_smg_names():
    for path in DESIGN_ROOT.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "import smg_" not in source
        assert "from smg_" not in source


def test_logger_writes_only_to_configured_data_folder(tmp_path):
    logger.configure(tmp_path / "logs" / "design-tools.log")
    logger.log("started")
    assert (tmp_path / "logs" / "design-tools.log").read_text().endswith("started\n")
```

- [ ] **Step 2: Run and verify RED**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_design_namespace.py tests\unit\test_design_logger.py -v
```

- [ ] **Step 3: Mechanically copy and rename the preserved modules**

Copy `smg_context.py`, `smg_core.py`, `smg_logger.py`, and every non-profile
command module into the namespaced package. Remove the `smg_` prefix from file
names and replace global imports with relative imports:

```python
from . import context as ctx
from . import core
from . import logger
from . import stub_arms as base
from . import stub_arms_export as stub_export
```

Copy all command icon folders used by migrated modules under
`commands/design/resources`.

- [ ] **Step 4: Narrow exception syntax without changing fallback intent**

Mechanically replace bare `except:` with `except Exception:`. Keep a silent pass
only for a capability probe that has an adjacent comment naming the unsupported
Fusion property or API variant. At command boundaries, log the traceback and
show a concise user message.

- [ ] **Step 5: Replace mutable install logging**

`logger.configure` defaults to:

```text
%USERPROFILE%\Documents\PhilsFusionTools\logs\design-tools.log
```

Create parent folders lazily. Never derive the log location from `__file__`.

- [ ] **Step 6: Compile, test, and commit**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_design_namespace.py tests\unit\test_design_logger.py -v
.\.venv\Scripts\python.exe -m compileall -q Addin\PhilsFusionTools\philsfusion\commands\design
git add Addin/PhilsFusionTools/philsfusion/commands/design tests/unit/test_design_namespace.py tests/unit/test_design_logger.py
git commit -m "refactor: namespace the preserved design engine"
```

---

### Task 4: Consolidate Six Profile Commands Into Create Steel Member

**Files:**
- Create: `Addin/PhilsFusionTools/philsfusion/commands/design/profile_schema.py`
- Create: `Addin/PhilsFusionTools/philsfusion/commands/design/steel_member.py`
- Create: `tests/unit/test_profile_schema.py`
- Create: `tests/unit/test_steel_member_contract.py`

**Interfaces:**
- Consumes: geometry functions and section tables from
  `philsfusion.commands.design.core`.
- Produces:
  - `ProfileFamily(key, label, fields, default_section, legacy_id)`.
  - `PROFILE_FAMILIES`.
  - `visible_field_ids(family_key) -> tuple[str, ...]`.
  - `SteelMemberCommandCreatedHandler(default_family: str | None = None)`.
  - `legacy_profile_handlers() -> dict[str, CommandCreatedEventHandler factory]`.

- [ ] **Step 1: Write failing schema tests**

```python
def test_profile_schema_covers_every_legacy_family_once():
    assert tuple(family.key for family in PROFILE_FAMILIES) == (
        "EA", "SHS", "RHS", "I_BEAM", "PFC", "C_CHANNEL"
    )
    assert len({family.legacy_id for family in PROFILE_FAMILIES}) == 6


def test_switching_family_exposes_only_relevant_fields():
    assert visible_field_ids("SHS") == (
        "lines", "size", "thickness", "extra", "profile_name", "angle"
    )
    assert "section" in visible_field_ids("PFC")
    assert "hole_diameter" in visible_field_ids("EA")
```

- [ ] **Step 2: Run and verify RED**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_profile_schema.py tests\unit\test_steel_member_contract.py -v
```

- [ ] **Step 3: Implement the pure profile schema**

Encode defaults from the preserved six modules. Validate family keys, positive
dimensions, section membership, and orientation values `0`, `90`, `180`, or
`270`.

- [ ] **Step 4: Implement one Fusion dialog**

The command contains:

- A family dropdown.
- One shared sketch-line selection.
- A family-specific options group.
- Shared extra-end, profile-name, and orientation inputs.
- EA hole/fillet controls.
- SHS/RHS dimension controls.
- I Beam/PFC/C Channel section dropdowns.

`inputChanged` toggles family-specific controls. `execute` dispatches directly
to `core.generate_ea_from_lines`, `generate_shs_from_lines`,
`generate_rhs_from_lines`, `generate_ub_from_lines`,
`generate_pfc_from_lines`, or `generate_c_channel_from_lines`.

- [ ] **Step 5: Add hidden compatibility handlers**

Each old profile ID creates the same dialog with its family preselected. It uses
the shared execution code and adds no toolbar control.

- [ ] **Step 6: Test and commit**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_profile_schema.py tests\unit\test_steel_member_contract.py -v
git add Addin/PhilsFusionTools/philsfusion/commands/design/profile_schema.py Addin/PhilsFusionTools/philsfusion/commands/design/steel_member.py tests/unit/test_profile_schema.py tests/unit/test_steel_member_contract.py
git commit -m "feat: consolidate steel member creation"
```

---

### Task 5: Bind Every Remaining Design Command And Alias

**Files:**
- Create: `Addin/PhilsFusionTools/philsfusion/commands/design/bindings.py`
- Modify: `Addin/PhilsFusionTools/philsfusion/app.py`
- Modify: `Addin/PhilsFusionTools/philsfusion/commands/specs.py`
- Create: `tests/unit/test_design_bindings.py`

**Interfaces:**
- Consumes: `ModuleCommandAction`, the namespaced command modules, and the production registry.
- Produces: `build_design_actions() -> dict[str, CommandAction]`.

- [ ] **Step 1: Write a failing one-to-one binding test**

```python
def test_every_design_handler_key_has_one_action_and_all_aliases_are_hidden():
    actions = build_design_actions()
    design_specs = [spec for spec in build_command_registry().ordered()
                    if spec.group not in {"BOM", "Help"}]

    assert set(actions) == {spec.handler_key for spec in design_specs}
    assert all(action.visible_control_count == 1 for action in actions.values())
    assert set().union(*(action.legacy_ids for action in actions.values())) == (
        set(LEGACY_ALIAS_IDS) - BOM_LEGACY_IDS
    )
```

- [ ] **Step 2: Run and verify RED**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_design_bindings.py -v
```

- [ ] **Step 3: Map canonical commands to handler classes**

The binding table names the exact module and class for each command. Split Body
uses `SplitCreatedHandler`; Delete Split Bodies uses
`SplitDeleteCreatedHandler`. Create Steel Member uses its custom action. All
other commands use the preserved command-created handler class in their
namespaced module.

- [ ] **Step 4: Initialize and clear shared context**

`PhilsFusionApplication.start` calls `design.context.init(app, ui)` before the
lifecycle starts. `stop` disposes the lifecycle first, then calls
`design.context.clear_handlers`. A failed startup performs both cleanup paths.

- [ ] **Step 5: Run catalog, binding, and lifecycle tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_command_catalog.py tests\unit\test_design_bindings.py tests\unit\test_lifecycle.py -v
```

- [ ] **Step 6: Commit**

```powershell
git add Addin/PhilsFusionTools/philsfusion/commands/design/bindings.py Addin/PhilsFusionTools/philsfusion/app.py Addin/PhilsFusionTools/philsfusion/commands/specs.py tests/unit/test_design_bindings.py
git commit -m "feat: bind all design commands and aliases"
```

---

### Task 6: Apply Balanced Preflight And Result Reporting

**Files:**
- Create: `Addin/PhilsFusionTools/philsfusion/commands/design/safety_bridge.py`
- Modify: `Addin/PhilsFusionTools/philsfusion/commands/design/context.py`
- Modify: high-risk modules under `Addin/PhilsFusionTools/philsfusion/commands/design`
- Create: `tests/unit/test_design_safety.py`

**Interfaces:**
- Consumes: `PreflightPlan`, `PlannedChange`, `ExecutionResult`,
  `format_preflight`, and `format_result`.
- Produces:
  - `confirm_plan(ui, plan) -> bool`.
  - `confirm_overwrite(ui, path: Path, summary: str) -> bool`.
  - `show_result(ui, result) -> None`.

- [ ] **Step 1: Write failing confirmation tests**

```python
def test_routine_plan_runs_without_extra_dialog(fake_ui):
    assert confirm_plan(fake_ui, routine_plan) is True
    assert fake_ui.messages == []


def test_destructive_plan_requires_explicit_yes(fake_ui):
    fake_ui.next_result = DialogResults.DialogNo
    assert confirm_plan(fake_ui, destructive_plan) is False
    assert "Risk: destructive" in fake_ui.messages[0].text


def test_existing_output_requires_overwrite_confirmation(tmp_path, fake_ui):
    path = tmp_path / "parts.xlsx"
    path.write_bytes(b"old")
    fake_ui.next_result = DialogResults.DialogNo
    assert confirm_overwrite(fake_ui, path, "Export 12 parts") is False
```

- [ ] **Step 2: Run and verify RED**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_design_safety.py -v
```

- [ ] **Step 3: Implement the bridge**

Use Fusion Yes/No dialogs only when `plan.requires_confirmation` is true.
Blocking errors show an error dialog and return false. Cancellation returns a
structured result with no succeeded or failed entries.

- [ ] **Step 4: Patch explicit operation boundaries**

Add preflight after selections/inputs are known but before mutation in:

- Component Set, Wireframe, Rotate, Batch Rename.
- Split Body and Delete Split Bodies.
- Move Preserve Position and Bulk Replace Components.
- Hole Cut, Stub Arms, Stub Arm Pair, and Set Stub Arm Bracket.
- Sort, Remove Length, Normalize Structure, and Fix Descriptions.
- Every export after its final path is known.

Each plan identifies selected component/body/line counts without logging
document names or geometry. Each command reports succeeded, skipped, failed,
and recovery counts.

- [ ] **Step 5: Add an AST policy test**

Assert every non-routine handler module contains a call to `confirm_plan` or
`confirm_overwrite`. Assert no migrated module contains bare `except:`.

- [ ] **Step 6: Test and commit**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_design_safety.py tests\unit\test_safety.py -v
git add Addin/PhilsFusionTools/philsfusion/commands/design tests/unit/test_design_safety.py
git commit -m "feat: add balanced preflight to design commands"
```

---

### Task 7: Migrate BOM Domain Logic And Settings

**Files:**
- Create: `Addin/PhilsFusionTools/philsfusion/commands/bom/__init__.py`
- Create: `Addin/PhilsFusionTools/philsfusion/commands/bom/domain.py`
- Create: `Addin/PhilsFusionTools/philsfusion/commands/bom/settings_bridge.py`
- Create: `Addin/PhilsFusionTools/philsfusion/commands/bom/legacy.py`
- Create: `Addin/PhilsFusionTools/philsfusion/commands/bom/resources/**`
- Modify: `Addin/PhilsFusionTools/philsfusion/services/settings.py`
- Create: `tests/unit/test_bom_domain.py`
- Create: `tests/unit/test_bom_settings_bridge.py`

**Interfaces:**
- Consumes: preserved `_PhilsBom.py`, old plist settings, `SettingsStore`, and
  `migrate_bom_settings`.
- Produces:
  - Pure BOM naming, CSV escaping, row sorting, and item-sequence helpers.
  - `BomSettingsBridge.load_legacy() -> dict`.
  - `BomSettingsBridge.save_legacy(settings: Mapping) -> None`.
  - One-time plist migration status in `settings.json`.

- [ ] **Step 1: Write characterization tests before moving logic**

```python
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Bracket:1", "Bracket"),
        ("Bracket (3)", "Bracket"),
        ("EA1-50x50x3", ("EA1", "50x50x3")),
    ],
)
def test_preserved_bom_name_rules(raw, expected):
    ...


def test_csv_cells_escape_delimiters_quotes_and_newlines():
    assert csv_cell('A,\"B\"\\nC', ",") == '"A,""B""\\nC"'
```

- [ ] **Step 2: Run characterization tests against extracted pure helpers**

Expected: RED until `domain.py` exists, then GREEN with behavior matching the
legacy functions.

- [ ] **Step 3: Copy the BOM runtime into its namespace**

Copy `_PhilsBom.py` to `commands/bom/legacy.py`, resources to
`commands/bom/resources`, remove obsolete update/download code, and import pure
helpers from `domain.py`. Keep Fusion geometry collection behavior unchanged
until smoke testing.

- [ ] **Step 4: Implement JSON settings compatibility**

On first load:

1. Read `%USERPROFILE%\Documents\PhilsFusionTools\settings.json`.
2. If no completed BOM migration exists, read
   `%USERPROFILE%\Documents\PhilsBom\PhilsBom-Settings.plist`.
3. Validate values through the legacy normalization rules.
4. Save mapped values atomically into the `bom` section.
5. Record source path, source hash, UTC timestamp, and status `completed`.
6. Never delete the old plist.

`load_legacy` maps JSON keys back to the old in-memory key names so the existing
settings dialog remains behavior-compatible.

- [ ] **Step 5: Test corrupt, missing, and repeated migrations**

Repeated migration is idempotent. A corrupt plist is reported as `skipped` with
an error reason and does not overwrite valid JSON settings.

- [ ] **Step 6: Commit**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_bom_domain.py tests\unit\test_bom_settings_bridge.py tests\unit\test_settings.py -v
git add Addin/PhilsFusionTools/philsfusion/commands/bom Addin/PhilsFusionTools/philsfusion/services/settings.py tests/unit/test_bom_domain.py tests/unit/test_bom_settings_bridge.py
git commit -m "feat: migrate BOM domain and settings"
```

---

### Task 8: Make BOM UI And Every Export Atomic

**Files:**
- Create: `Addin/PhilsFusionTools/philsfusion/commands/bom/exporters.py`
- Create: `Addin/PhilsFusionTools/philsfusion/commands/bom/action.py`
- Modify: `Addin/PhilsFusionTools/philsfusion/commands/bom/legacy.py`
- Modify: `Addin/PhilsFusionTools/philsfusion/app.py`
- Create: `tests/unit/test_bom_exporters.py`
- Create: `tests/unit/test_bom_action.py`

**Interfaces:**
- Consumes: CSV text from legacy collection, atomic file services, BOM handlers,
  and the canonical BOM specs.
- Produces:
  - `build_payload(csv_text: str, export_type: str) -> bytes`.
  - `validate_payload(payload: bytes, export_type: str) -> None`.
  - `BomCommandAction`.
  - Optional marking-menu registration owned by the lifecycle.

- [ ] **Step 1: Write failing payload tests**

```python
@pytest.mark.parametrize("export_type", ["CSV (.csv)", "XML (.xml)", "JSON (.json)", "XLSX (.xlsx)"])
def test_every_bom_payload_validates(export_type):
    payload = build_payload("Part,Qty\\nBracket,2\\n", export_type)
    validate_payload(payload, export_type)


def test_failed_xlsx_validation_preserves_existing_file(tmp_path):
    target = tmp_path / "bom.xlsx"
    target.write_bytes(b"old")
    with pytest.raises(ValueError):
        atomic_write_bytes(target, b"bad", validator=validate_xlsx)
    assert target.read_bytes() == b"old"
```

- [ ] **Step 2: Run and verify RED**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_bom_exporters.py -v
```

- [ ] **Step 3: Implement in-memory exporters**

- CSV: UTF-8 bytes with the selected delimiter.
- JSON: parse with `csv.DictReader`, encode a list of objects.
- XML: escape element names and text, parse with `ElementTree`.
- XLSX: generate the existing minimal workbook into `io.BytesIO`, then open it
  with `zipfile.ZipFile` and require workbook and worksheet entries.

No converter writes or deletes an intermediate CSV file.

- [ ] **Step 4: Replace direct BOM writes**

After folder/name selection, calculate the real extension before checking the
target. Build a `PreflightPlan` containing output path, row count, export type,
and overwrite warning. On approval, call `atomic_write_bytes` with the matching
validator. Show a structured result with the final path.

- [ ] **Step 5: Bind canonical and legacy BOM definitions**

Expose `PhilsFusionTools_CreateBOM` and `PhilsFusionTools_BOMSettings` in the BOM
group. Create hidden definitions for `PhilsBom_contextMenuButton1` and
`PhilsBom_contextMenuButton2`. If the optional marking menu is enabled, it uses
the canonical definitions and its event handler is removed on stop.

- [ ] **Step 6: Test and commit**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_bom_exporters.py tests\unit\test_bom_action.py -v
git add Addin/PhilsFusionTools/philsfusion/commands/bom Addin/PhilsFusionTools/philsfusion/app.py tests/unit/test_bom_exporters.py tests/unit/test_bom_action.py
git commit -m "feat: add atomic BOM commands and exports"
```

---

### Task 9: Polish Resources, Help, Diagnostics, And Package

**Files:**
- Create: `Addin/PhilsFusionTools/resources/<group>/*.svg`
- Create: `Addin/PhilsFusionTools/resources/<command>/*.svg`
- Create: `Addin/PhilsFusionTools/philsfusion/services/health.py`
- Create: `Addin/PhilsFusionTools/philsfusion/services/logging.py`
- Create: `Addin/PhilsFusionTools/philsfusion/commands/help.py`
- Modify: `Addin/PhilsFusionTools/philsfusion/services/diagnostics.py`
- Modify: `Addin/PhilsFusionTools/philsfusion/app.py`
- Modify: `release/package-allowlist.txt`
- Modify: `tools/package_phils_fusion_tools.ps1`
- Modify: `tests/test_package_contents.py`
- Create: `tests/unit/test_health.py`
- Create: `tests/unit/test_help.py`

**Interfaces:**
- Consumes: package build info, registry, settings migration, and lifecycle
  startup state.
- Produces:
  - `write_health(path, snapshot)`.
  - `About And Migration` command.
  - Production ZIP `PhilsFusionTools-2.0.0.zip`.

- [ ] **Step 1: Write failing health and package tests**

```python
def test_health_snapshot_proves_exact_runtime_identity(tmp_path):
    write_health(tmp_path / "health.json", healthy_snapshot)
    data = json.loads((tmp_path / "health.json").read_text())
    assert data["status"] == "healthy"
    assert data["public_commands"] == 25
    assert len(data["package_fingerprint"]) == 64


def test_production_package_has_no_legacy_roots(production_package):
    names = production_package_names(production_package)
    assert not any(name.startswith("PhilsDesignTools/") for name in names)
    assert not any(name.startswith("PhilsBom.bundle/") for name in names)
```

- [ ] **Step 2: Create a coherent icon system**

Use simple high-contrast SVG line icons with a warm orange, steel blue, and
charcoal palette. Each group receives a distinct symbol. Commands reuse legacy
icons only where they remain clear at 16 and 32 pixels. Do not add bitmap caches
or design-source files to the package.

- [ ] **Step 3: Add About/Migration and health output**

About/Migration shows version, source commit, package hash, public command
count, compatibility alias count, settings migration state, legacy quarantine
state, log folder, and rollback pointer. Startup writes `health.json` atomically
only after all seven groups and 25 commands register successfully.

- [ ] **Step 4: Add bounded logs**

Write startup, command result, migration, and installer-readable health messages
to `Documents\PhilsFusionTools\logs`. Rotate at 2 MiB and keep three prior logs.
Never log design names, selected geometry, file contents, or exported rows.

- [ ] **Step 5: Promote the packager to production**

Add `-Production`. It still refuses `-Install`, requires clean runtime source,
packages only explicit allow-list entries, validates every Python file and
resource, embeds `artifact: production`, and emits ZIP plus SHA-256 sidecar.

- [ ] **Step 6: Run tests and commit**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_health.py tests\unit\test_help.py tests\test_package_contents.py -v
git add Addin/PhilsFusionTools release/package-allowlist.txt tools/package_phils_fusion_tools.ps1 tests
git commit -m "feat: polish help health and production package"
```

---

### Task 10: Build A Transactional Windows Installer And Migration Finalizer

**Files:**
- Create: `tools/install_phils_fusion_tools.ps1`
- Create: `tools/finalize_phils_fusion_tools_migration.ps1`
- Create: `tools/rollback_phils_fusion_tools.ps1`
- Create: `tests/powershell/test_installer_contract.ps1`
- Create: `docs/operations/install-and-rollback.md`

**Interfaces:**
- Consumes: production ZIP, sidecar hash, verified rollback pointer, Fusion
  process state, and startup `health.json`.
- Produces:
  - Staged unified install.
  - Legacy quarantine outside Autodesk scan paths.
  - Final timestamped legacy archive after health verification.
  - One-command rollback.

- [ ] **Step 1: Write failing installer contract tests**

The PowerShell test uses temporary fake APPDATA/Documents roots and asserts:

```powershell
It "refuses install while Fusion is running"
It "rejects a package with the wrong SHA-256"
It "quarantines every configured legacy path before activation"
It "restores all paths when health verification fails"
It "finalizes only when health package hash matches the installed package"
It "leaves exactly one manifest below the fake Fusion AddIns root"
```

- [ ] **Step 2: Run and verify RED**

```powershell
Invoke-Pester tests\powershell\test_installer_contract.ps1 -Output Detailed
```

Expected: failure because the installer scripts do not exist.

- [ ] **Step 3: Implement stage installation**

The installer:

1. Requires Fusion, FusionLauncher, and FusionService processes to be closed.
2. Verifies the production ZIP SHA-256 and exact allow-list.
3. Verifies the rollback root and rollback manifest hash.
4. Creates a timestamped transaction folder under
   `Documents\PhilsFusionTools\MigrationTransactions`.
5. Moves the six recorded legacy paths into transaction quarantine using
   literal, fully resolved paths.
6. Extracts the unified package into a sibling staging folder.
7. Compiles Python and validates the manifest.
8. Moves any prior unified install into transaction quarantine.
9. Atomically renames staging to the final AddIns folder.
10. Writes transaction state `awaiting_health`.

- [ ] **Step 4: Implement health finalization**

The finalizer requires:

- `health.json` status `healthy`.
- Health package fingerprint equals the installed package tree hash.
- Version `2.0.0`.
- Seven groups and 25 public commands.
- No startup errors.

It then moves transaction quarantine to
`Documents\PhilsFusionTools\LegacyArchive\<timestamp>`, writes a signed-by-hash
migration receipt, and marks the transaction `complete`.

- [ ] **Step 5: Implement rollback**

Rollback requires Fusion closed, removes only the transaction's installed
unified folder after verifying its recorded hash, and restores every quarantined
legacy path to its exact original location. It never deletes the verified
pre-2.0 rollback set.

- [ ] **Step 6: Test and commit**

```powershell
Invoke-Pester tests\powershell\test_installer_contract.ps1 -Output Detailed
git add tools/install_phils_fusion_tools.ps1 tools/finalize_phils_fusion_tools_migration.ps1 tools/rollback_phils_fusion_tools.ps1 tests/powershell/test_installer_contract.ps1 docs/operations/install-and-rollback.md
git commit -m "feat: add transactional Windows migration installer"
```

---

### Task 11: Complete Release Verification, Install, And GitHub Parity

**Files:**
- Create: `docs/verification/release-2.0.0-verification.md`
- Modify: `Addin/CHANGELOG.md`
- Modify: `Addin/README.md`

**Interfaces:**
- Consumes: all prior commits, production package, installer, Fusion health
  read-back, and GitHub origin.
- Produces: installed version 2.0.0, archived legacy add-ins, release evidence,
  and a remote branch exactly matching the local release commit.

- [ ] **Step 1: Run the complete offline gate**

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\run_quality.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\package_phils_fusion_tools.ps1 -Production
Invoke-Pester tests\powershell\test_installer_contract.ps1 -Output Detailed
git diff --check
git status --short
```

Expected: all pytest, Ruff, compile, package, Pester, and whitespace checks pass.

- [ ] **Step 2: Run the rollback verifier again**

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Users\phil9\Documents\PhilsFusionTools-Rollback\20260730-111056\verify-rollback.ps1
```

Expected: passed with the original manifest hash.

- [ ] **Step 3: Stage install with Fusion closed**

Run the transactional installer. Read back the installed manifest and complete
tree hash. Confirm all legacy paths are present in transaction quarantine and
absent from Autodesk scan paths.

- [ ] **Step 4: Start Fusion and verify startup health**

Start Fusion normally. Wait for `health.json`, then verify version, hash, group
count, command count, settings migration, and zero startup errors. Stop and
start the add-in from Scripts and Add-Ins once, then confirm the health sequence
increments without duplicate controls.

- [ ] **Step 5: Run representative command smoke tests**

Using a disposable Fusion design:

- Create Steel Member with EA and PFC.
- Rotate one created member.
- Create and delete a split body, rejecting confirmation once first.
- Create a stub arm and export its report to a temporary folder.
- Run one cleanup command and inspect its result counts.
- Export CSV and XLSX BOM files, validate both, and reject one overwrite.
- Open Diagnostics and About/Migration.

Undo or close the disposable design without saving. Record command outcomes and
export hashes.

- [ ] **Step 6: Finalize migration**

Close Fusion, run the finalizer, and verify:

- One `PhilsFusionTools` add-in exists in API AddIns.
- No Phils BOM or Phils Design Tools legacy folder remains in any Autodesk scan
  path.
- The timestamped legacy archive contains all six quarantined paths.
- The verified pre-2.0 rollback set remains unchanged.

- [ ] **Step 7: Commit release evidence**

Update changelog, README, and release verification with exact test counts,
package hash, installed tree hash, health snapshot hash, legacy archive path,
rollback hash, and smoke-test results.

```powershell
git add Addin/CHANGELOG.md Addin/README.md docs/verification/release-2.0.0-verification.md
git commit -m "release: verify Phils Fusion Tools 2.0.0"
```

- [ ] **Step 8: Push and verify GitHub parity**

```powershell
git push -u origin codex/phils-fusion-tools-2.0
git fetch origin codex/phils-fusion-tools-2.0
git rev-parse HEAD
git rev-parse origin/codex/phils-fusion-tools-2.0
git diff --quiet HEAD origin/codex/phils-fusion-tools-2.0
```

Expected: local and remote commit IDs are identical and the diff exits zero.

## Plan Self-Review

- Spec coverage: rollback, one plugin, grouped UI, balanced prompts, profile
  consolidation, aliases, settings migration, atomic files, diagnostics,
  health, Windows installation, legacy archive, Fusion smoke testing, and
  GitHub parity all have explicit tasks.
- Placeholder scan: no unresolved markers or unspecified implementation steps remain.
- Type consistency: command specs produce handler keys consumed by action maps;
  actions return lifecycle-owned installations; safety bridges consume the
  foundation contracts; health consumes the package fingerprint used by the
  finalizer.
- API constraint check: aliases attach shared handlers and do not call
  `CommandDefinition.execute` from command events.
