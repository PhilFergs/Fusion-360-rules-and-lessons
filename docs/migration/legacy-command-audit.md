# Phils BOM And Design Tools Legacy Audit

Audit date: 2026-07-30

This audit covers the preserved source in `PhilsBom.bundle` and
`Addin/PhilsDesignTools`, plus the verified installed snapshot captured at:

`C:\Users\phil9\Documents\PhilsFusionTools-Rollback\20260730-111056`

## Scope And Evidence

- Design Tools: 83 files, including 27 Python files and 54 command icon files.
- BOM bundle: 43 files, including a 2,935-line runtime module.
- Design command modules: 24 modules producing 25 current command definitions.
- BOM commands: Create BOM and Phils BOM Settings.
- Python target: Fusion CPython 3.10.
- Static syntax/undefined-name gate: passed for both legacy trees.
- Existing legacy unit tests: none.
- Design Tools bare `except:` blocks: 469.
- Design Tools silent `except: pass` blocks: 332.
- BOM bare `except:` blocks: zero.

## Findings

### High: Reloads Can Retain Duplicate Design Event Handlers

Every Design Tools module owns its own `register` function. Most functions reuse
an existing command definition and attach another `commandCreated` handler. The
shared `smg_context.init` function does not clear its handler list on re-entry,
and the legacy `stop` function deletes command definitions without clearing that
list.

Consequence: a stop/start or failed partial start can retain duplicate handlers,
create duplicate command inputs, or execute a command more than once.

Required correction: one lifecycle must own all controls, command definitions,
and handlers; startup must roll back partially created UI; stop must release
resources in reverse order.

### High: BOM Settings And Exports Are Not Transactional

The BOM writes settings directly with `plistlib.dump`. Export first writes CSV
directly to the final path, then converts it to XLSX, XML, or JSON and deletes
the CSV. A crash, conversion error, or invalid final payload can leave a partial
file or truncate an existing file.

Required correction: migrate settings once into versioned JSON and use atomic
temporary-file validation plus `os.replace` for every output format.

### High: Destructive And Bulk Operations Lack A Common Safety Contract

Split/delete, hole cutting, component replacement, occurrence moves, structure
normalization, and large rename operations execute from separate handlers.
There is no shared preflight summary, risk classification, confirmation rule,
or structured partial-failure result.

Required correction: every command receives a registry risk level. Bulk,
destructive, and overwrite operations must show a stable preflight summary.
Results must distinguish succeeded, skipped, failed, and recovery actions.

### Medium: Exception Handling Hides Operation Failures

Design Tools contains 469 bare catches and 332 silent passes. Some are reasonable
Fusion capability probes, but the same pattern is used around geometry moves,
renames, cleanup, and UI registration.

Required correction: mechanically narrow catches to `Exception`, retain silent
fallback only for documented capability probes, and route command-boundary
failures to the shared log and result summary.

### Medium: Runtime Logs Modify Installed Source

`smg_logger.py` writes `PhilsDesignTools.log` beside the Python modules. The
installed-state audit confirmed that this log changed after Fusion started and
stopped, while all 214 Python/resource files remained identical.

Required correction: write all logs under
`Documents\PhilsFusionTools\logs`, never in Fusion's scan path.

### Medium: Three BOM Copies Are Installed

The verified rollback contains BOM copies under ApplicationPlugins, API AddIns,
and MyScripts Autorun. This explains the earlier unreliable `.bundle`
installation behavior and creates a duplicate-load risk.

Required correction: install one folder named `PhilsFusionTools` under Fusion's
Windows API AddIns path. After a successful health check, archive every legacy
copy outside all Autodesk scan paths.

### Medium: The Toolbar Is Flat And Redundant

Design Tools currently registers about 25 controls into one panel. Six separate
steel-member commands duplicate selection, orientation, profile naming,
registration, and error-handling behavior.

Required correction: expose seven ordered groups and consolidate EA, SHS, RHS,
I Beam, PFC, and C Channel into one `Create Steel Member` command. Preserve the
six old IDs as hidden compatibility definitions for the 2.x transition.

### Low: Naming And Identity Are Inconsistent

Runtime IDs mix `PhilsBom`, `PhilsDesignTools`, and an old UUID. Generated files
and logs identify different products.

Required correction: new public IDs use `PhilsFusionTools_*`; legacy IDs exist
only in the compatibility map and are reported by diagnostics.

## Approved Command Layout

| Group | Public command | Risk | Legacy source |
|---|---|---:|---|
| BOM | Create BOM | File overwrite | `PhilsBom_contextMenuButton1` |
| BOM | BOM Settings | Routine | `PhilsBom_contextMenuButton2` |
| Create | Create Steel Member | Routine | EA, SHS, RHS, I Beam, PFC, C Channel |
| Create | New Component Set | Bulk | `PhilsDesignTools_ComponentSet` |
| Create | Wireframe From Body | Bulk | `PhilsDesignTools_WireframeFromBody` |
| Modify | Rotate Steel Member | Bulk | `PhilsDesignTools_Rotate` |
| Modify | Batch Rename | Bulk | `PhilsDesignTools_EA_BatchRename` |
| Modify | Split Body | Destructive | `PhilsDesignTools_SplitBody_V2` |
| Modify | Delete Split Bodies | Destructive | `PhilsDesignTools_SplitBody_Delete` |
| Modify | Move Preserve Position | Bulk | `PhilsDesignTools_MovePreservePosition` |
| Modify | Bulk Replace Components | Destructive | `PhilsDesignTools_BulkReplaceComponents` |
| Fabricate | Hole Cut From Face | Destructive | `PhilsDesignTools_HoleCutFromFace` |
| Fabricate | Stub Arms To Wall | Bulk | `PhilsDesignTools_StubArms` |
| Fabricate | Stub Arm Pair To Wall | Bulk | `PhilsDesignTools_StubArmPair` |
| Fabricate | Set Stub Arm Bracket | Bulk | `PhilsDesignTools_StubArms_SetBracket` |
| Export | Multi-Part Export | File overwrite | `PhilsDesignTools_IGES_Export` |
| Export | EA Hole Export | File overwrite | `PhilsDesignTools_EA_HoleExport_CSV` |
| Export | Stub Arms Export | File overwrite | `PhilsDesignTools_StubArms_Export_CSV` |
| Export | Stub Arms DXF | File overwrite | `PhilsDesignTools_StubArms_Export_DXF` |
| Cleanup | Sort Components | Bulk | `PhilsDesignTools_SortComponents` |
| Cleanup | Remove Length From Names | Bulk | `PhilsDesignTools_RemoveLengthNames` |
| Cleanup | Normalize Component Structure | Destructive | `PhilsDesignTools_NormalizeComponentStructure` |
| Cleanup | Fix Descriptions And Part Numbers | Bulk | `PhilsDesignTools_SetComponentDescriptions` |
| Help | Diagnostics | Routine | New |
| Help | About And Migration | Routine | New |

## Compatibility Policy

- The six profile-generator IDs remain executable but hidden for one major
  release and invoke the same shared profile implementations as the new command.
- Every non-consolidated Design Tools command receives a new
  `PhilsFusionTools_*` public ID and a hidden old-ID definition attached to the
  same command-created handler.
- The two BOM context-menu IDs remain hidden aliases for Create BOM and BOM
  Settings.
- Compatibility IDs never add toolbar controls.
- Diagnostics reports the active compatibility count and the planned removal
  version.

## Verification Boundary

Pure data transformation, settings, path planning, export payloads, catalog
coverage, safety rules, and lifecycle behavior are automated under pytest.
Fusion object-model behavior requires an installed smoke test because Autodesk's
`adsk` runtime is only available inside Fusion.

The Fusion smoke test must verify:

1. One `Phils Fusion Tools` panel appears.
2. Exactly seven ordered group controls appear.
3. Every public command opens without duplicate inputs.
4. Start, stop, and start again produce no duplicate controls or handlers.
5. A representative model passes create, modify, fabrication, export, cleanup,
   and BOM checks.
6. Cancellation and rejected confirmation leave the design and filesystem
   unchanged.
7. Diagnostics reports the installed package hash and healthy startup.

## Autodesk API Constraints

The implementation follows Autodesk's current API behavior:

- A drop-down exposes a `ToolbarControls` collection, so normal commands can be
  added inside each approved group.
- `ToolbarControls.addCommand` creates a control whose ID comes from its command
  definition.
- `CommandDefinition.execute` must not be called from any command event.
  Compatibility definitions therefore attach the same handler implementation
  instead of forwarding from one active command to another.
- API-created controls and definitions must be explicitly deleted during add-in
  shutdown.

References:

- https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/DropDownControl_controls.htm
- https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ToolbarControls_addCommand.htm
- https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/CommandDefinition_execute.htm
- https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/UserInterface_UM.htm
