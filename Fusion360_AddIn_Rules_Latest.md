# Fusion 360 Add-In Development Rules & Best Practices  
**Version: Latest (1.0.1+)**

This is the updated and expanded ruleset, based on `Fusion360_AddIn_Rules_v1_0_0.md`,  
with new sections:

- **v1.0.1 Additions**
- **Logging & Debugging Standards**

---

# 1. General Fusion 360 Scripting Principles

### 1.1 Full, Ready-to-Run Code
- Always generate complete working scripts.
- No partial snippets unless troubleshooting.
- Deliver full modules following project structure.

### 1.2 Module Separation
- `AddIn.py` — entry point  
- `Main.py` — core logic  
- `State.py` — shared/persistent state  
- `UI.py` — UI & events  
- `Geometry.py` — geometry generation  
- `Preview.py` — preview bodies  

### 1.3 Naming Conventions
- Descriptive names.
- Avoid cryptic or abbreviated identifiers.
- Use stable command/control IDs.

### 1.4 Exception Handling
```
try:
    ...
except:
    ui.messageBox(traceback.format_exc())
```

### 1.5 Unit Safety
- Always use `ValueInput.createByString()`.
- Never rely on user’s unit preferences.
- Convert units explicitly when needed.

---

# 2. Add-In Folder Structure Rules

### 2.1 Required Layout
```
MyAddIn/
    MyAddIn.py
    MyAddIn.manifest
    Modules/
        Main.py
        Geometry.py
        State.py
        UI.py
        Preview.py
```

### 2.2 Manifest Rules
- JSON format only.
- Must match folder + entry Python file.
- Required keys:
  - autodeskProduct  
  - type  
  - id  
  - version  
  - author  
  - description  
  - main

### 2.3 Version Sync
- Parent folder version matches manifest version.
- Semantic versioning: MAJOR.MINOR.PATCH.

---

# 3. EA Project Rules

### Sketch Export
- LineID starts at 1.
- Export start XYZ, end XYZ, length.
- No area calculations unless required.

### CSV Rules
- Comma-separated.
- Always include headers.
- UTF‑8 encoding.

### Geometry Rules
- Always create bodies inside components (never root unless required).
- Use construction geometry for stability.
- Prefer named parameters.

### Preview Rules
- Use temporary BReps.
- Delete preview entities on cancel or finalize.

---

# 4. UI & Event Rules

### Required Command Methods
- `onCreate`
- `onExecute`
- `onInputChanged`
- `onDestroy`

### Events
- Store handlers globally (`handlers = []`).
- Never allow handlers to be garbage collected.
- Remove or clean references on destroy.

### UI Panels
- Default panel: `SolidModifyPanel` or `Utilities` unless project specifies otherwise.

---

# 5. State Management Rules

### State Module (`State.py`)
- Central location for persistent values.
- Expose getters/setters.
- No geometry or UI logic inside state module.

### Globals
- Only store:
  - `app`
  - `ui`
  - event handler arrays

---

# 6. Coding Style Rules

- Explicit casting (`float()`, `int()`).
- Use small, readable functions.
- Comment geometry steps clearly.
- Use descriptive variable names.
- Prefer mathematical clarity over brevity.

---

# 7. Safety & Error Proofing

- Validate user selections.
- Fail safely with descriptive messages.
- Avoid using timeline indices.
- Avoid direct face references for persistent operations.
- Delete temporary bodies immediately after use.

---

# 8. GitHub Workflow

- Each add-in version in a unique versioned folder.
- Maintain `CHANGELOG.md`.
- `main` or `master` branch must always be runnable.
- Load the rules file before coding sessions.
- Use GitHub Releases for stable versions.

---

# 9. ChatGPT Collaboration Rules

- Generate ONE complete module per response.
- Use "safe delivery mode" (clean, orderly modules).
- Do NOT zip unless explicitly requested.
- Follow the Fusion 360 API conventions strictly.
- Ask clarifying questions if geometry ambiguity exists.

---

# 10. Future-Proofing

- Avoid deprecated API calls.
- Follow latest Fusion 360 API guidelines.
- Prefer construction geometry.
- Avoid referencing transient face IDs.
- Use assembly-context-native-context conversions for multi-component work.

---

# 11. v1.0.1 ADDITIONS  
*(New section added in the Latest Version)*

### 11.1 Assembly Context Transform Rules  
When working with bodies or faces from different components:
- Always convert from **native → world → target-native**.
- Use:
  - `entity.nativeObject`
  - `entity.assemblyContext`
  - `occurrence.transform`
  - `Matrix3D.invert()`

### 11.2 Deterministic UI Insertion  
- Always remove stale controls before inserting new ones:
```
ctrl = panel.controls.itemById(ID)
if ctrl:
    ctrl.deleteMe()
```

### 11.3 Resource Folder Requirements  
All commands must define a valid icon folder:
```
resources/<AddInName>/
    16.png
    32.png
    64.png
    128.png
```

### 11.4 Logging Required for All Production Tools  
All intermediate computations, especially transforms and coordinate conversions, must be logged.

---

# 12. Logging / Debugging Standards  
*(New section added in the Latest Version)*

### 12.1 Required Logger (EA_Logger.py)
Each add-in must include:
- `init_logger(name)`
- `log(message)`
- `log_exception(context)`

### 12.2 Logger Output Rules
- Logs are written to:
```
/logs/<AddInName>_log_YYYYMMDD_HHMMSS.txt
```
- Logs may never interrupt the add-in (fail-silent mode).

### 12.3 When to Log
Log:
- Occurrence transforms  
- Native vs world vs target coordinates  
- Axes, centers, geometry parameters  
- Execution start/end  
- Any branching logic  
- All exceptions  

### 12.4 Accepted Debug Workflow
- During development: keep tool bodies visible (`isKeepToolBodies=True`)
- For production: remove tool bodies after operations (`isKeepToolBodies=False`)
- For debugging transforms: log
  - native center
  - world center
  - target center
  - axis in all three spaces

---

End of File
