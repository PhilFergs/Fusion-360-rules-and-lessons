# Fusion 360 Add-In Development Rules & Best Practices  
**Version: v1.1.0 (SteelMemberGeneration Edition)**

This ruleset defines the official architecture, coding standards, geometry rules, and rotation conventions for all Fusion 360 add-ins in this ecosystem.  
It consolidates knowledge from dozens of add-ins such as SteelMemberGeneration, EA_AddIn v4.x, hole-cutting tools, profile generators, and preview systems.

---

# 📘 Table of Contents
- [1. General Scripting Principles](#1-general-scripting-principles)
- [2. Add-In Folder Structure](#2-add-in-folder-structure)
- [3. Steel-Member Geometry Rules](#3-steel-member-geometry-rules)
- [4. UI & Event Rules](#4-ui--event-rules)
- [5. State Management](#5-state-management)
- [6. Coding Style](#6-coding-style)
- [7. Safety & Error-Proofing](#7-safety--error-proofing)
- [8. GitHub Workflow](#8-github-workflow)
- [9. ChatGPT Collaboration Rules](#9-chatgpt-collaboration-rules)
- [10. Future-Proofing](#10-future-proofing)
- [11. Assembly Context & Transform Rules](#11-assembly-context--transform-rules)
- [12. Logging & Debugging Standards](#12-logging--debugging-standards)
- [13. SteelMemberGeneration Lessons (NEW)](#13-steelmembergeneration-lessons-v110-new)

---

# 1. General Scripting Principles

## 1.1 Complete, Ready-to-Run Code
- Deliver full modules, not fragments.  
- No reliance on earlier messages.  
- Must run standalone in Fusion.

## 1.2 Required Module Separation
```
<AddInName>.py        ← Entry script
smg_context.py        ← App/UI access + handler registry
smg_core.py           ← Utility functions
smg_ea.py             ← EA member logic
smg_shs.py            ← SHS member logic
smg_rhs.py            ← RHS member logic
smg_rotate.py         ← Rotation logic
__init__.py           ← Required for multi-file add-ins
```

## 1.3 Naming Rules
- Folder, manifest `id`, and entry script name must match.  
- Maintain stable command IDs.  

## 1.4 Exception Handling
```python
try:
    ...
except:
    ui.messageBox("Error:\n" + traceback.format_exc())
```

## 1.5 Unit Safety
- Always use `ValueInput.createByString("50 mm")`.  
- `.value` returns Fusion internal units (cm).  

---

# 2. Add-In Folder Structure

## 2.1 Required Layout
```
<AddInName>/
    <AddInName>.py
    <AddInName>.manifest
    __init__.py
    smg_context.py
    smg_core.py
    smg_ea.py
    smg_rhs.py
    smg_shs.py
    smg_rotate.py
    resources/
        16.png
        32.png
        64.png
        128.png
```

## 2.2 Manifest Rules
- Must be JSON.  
- `id` and entry script must match folder name.  

## 2.3 Version Sync
- Version in manifest = version folder name.  
- Follow semantic versioning.

---

# 3. Steel-Member Geometry Rules

## 3.1 Component Generation
- All geometry must be created inside a new component.

## 3.2 Deterministic Orientation
- Member length axis is always **local Y-axis**.

## 3.3 Fillet Standards (AS/NZS 1163)
- Internal radius = thickness  
- External radius = thickness + 2  

## 3.4 EA Geometry Rules
- Root fillet radius = thickness  
- Hole pattern exists on bottom flange  
- Geometry must be stable and symmetric

---

# 4. UI & Event Rules

## 4.1 SelectionCommandInput Rules
- Single selection:
```
sel.setSelectionLimits(1, 1)
```
- Multi-selection:
```
sel.setSelectionLimits(1, 0)
```
- Never use global `Selections`.

## 4.2 Fusion UI Quirks
- DropDown list items use `.name`, not `.text`.  
- `.selectionCount` is unreliable → loop using index access.

## 4.3 Required Command Lifecycle
```
onCreate
onExecute
onInputChanged
onDestroy
```

## 4.4 UI Panel Rules
- Remove stale controls before adding new ones.

---

# 5. State Management

## 5.1 What State May Contain
- app  
- ui  
- handler arrays  
- user presets  

## 5.2 Forbidden
- geometry references  
- persistent faces  
- construction entities  

---

# 6. Coding Style

- Clear variable names  
- Avoid deep nesting  
- Comment geometry steps  
- Prefer readability over brevity  

---

# 7. Safety & Error-Proofing

- Validate selections  
- Never depend on timeline indices  
- Use construction geometry where possible  
- Delete preview bodies immediately  

---

# 8. GitHub Workflow

- Each release in a versioned folder  
- Maintain `CHANGELOG.md`  
- `main` branch must stay runnable  
- Store this ruleset in repo root  

---

# 9. ChatGPT Collaboration Rules

## 9.1 Delivery Rules
- One complete module per response  
- Never zip unless asked  
- Must follow ruleset  
- Ask clarifying questions only when needed  

---

# 10. Future-Proofing

- Avoid deprecated Fusion APIs  
- Avoid face references for long-term operations  
- Use matrix transforms for all context conversions  
- Prefer construction geometry and constraints  

---

# 11. Assembly Context & Transform Rules

## 11.1 Required Transform Pattern
```
native → world → target-native
```

## 11.2 APIs Used
- `nativeObject`  
- `assemblyContext`  
- `occurrence.transform`  
- `Matrix3D.invert()`  

---

# 12. Logging & Debugging Standards

## 12.1 Required Logger
Each add-in must include:
- `log(message)`  
- `log_exception(context)`  
- Timestamp format  
- Silent failure mode  

## 12.2 Required Logging
- Selection results  
- Axes (native + world)  
- Centers (native + world)  
- Occ transforms  
- Execution start/end  
- Exceptions  

## 12.3 Debugging Workflow
- Keep tool bodies visible during development  
- Remove tool bodies in production  
- Log:
  - native center  
  - world center  
  - axis vectors  

## 12.4 New Tool Debug Logging (REQUIRED)
- Every new command must include a `DEBUG_<TOOL>` flag and emit debug logs via the shared logger.  
- Log per-item failures (why a selection/operation was skipped) and critical geometry decisions.  
- Keep debug logs lightweight but sufficient to reproduce failure conditions.  

---

# 13. SteelMemberGeneration Lessons (v1.1.0 NEW)

## 13.1 Add-In Loading Requirements
To prevent Fusion’s “add-in stays OFF” bug:
- Must include `__init__.py`  
- Must patch `sys.path` at top of `run()`  
- Must delete stale `__pycache__` after restructuring  

Example:
```python
this_dir = os.path.dirname(os.path.realpath(__file__))
if this_dir not in sys.path:
    sys.path.append(this_dir)
```

---

## 13.2 Rotation Standards (CRITICAL)

### 13.2.1 EA Rotation Standard (Use Hole-Centre Axis)
EA rotation must always use:

**Axis Determination**
1. Scan circular edges  
2. Extract hole centres  
3. Find farthest-apart pair  
4. Axis = vector between them  
5. Pivot = midpoint  

This reproduces correct commercial EA rotation (matches EA_AddIn v4.0.0).

### 13.2.2 SHS / RHS Rotation Standard
- Axis = local Y-axis transformed to world  
- Pivot = bounding-box centre  
- Behaviour = pure twist around member centreline  

### 13.2.3 Classification Rule
```
if component.name.startswith("EA"):
    use_hole_centre_rotation()
else:
    use_length_axis_rotation()
```

---

## 13.3 Selection Lessons
- `.selectionCount` may be wrong → always iterate using index  
- Do not use global Selections collection for commands  

---

## 13.4 Dropdown Lessons
- Fusion uses `.name` instead of `.text` for list items  

---

## 13.5 Geometry Interpretation Lessons
- Bottom-flange detection by face is unreliable → always use hole centre axis  
- SHS/RHS rotate cleanly using length axis + bbox centre  

---

## 13.6 UI Lessons
- Avoid blocking modal dialogs for geometry operations  
- Rotation commands should remain open unless explicitly closed  

---

## 13.7 Debugging Lessons
- Ensure logger writes to add-in folder  
- Log entry into every handler  
- Write test files to confirm write permissions  

---

# End of Document — v1.1.0
