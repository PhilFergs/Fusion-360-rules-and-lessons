# Fusion 360 Add-In Development Rules & Best Practices  
**Version: 1.0.0**

This is the Markdown version of the official Fusion 360 add-in development rules.  
Functionally identical to the TXT version, but GitHub-optimized.

---

## 1. General Fusion 360 Scripting Principles

### 1.1 Full, Ready-to-Run Code
- Always generate complete working scripts.
- No partial snippets unless troubleshooting.

### 1.2 Module Separation
- `EA_AddIn.py` — entry point  
- `EA_Main.py` — core logic  
- `EA_State.py` — state/config  
- `EA_UI.py` — UI & events  
- `EA_Geometry.py` — geometry generation  
- `EA_Preview.py` — previews  

### 1.3 Naming Conventions
- Use descriptive names.
- Avoid vague or abbreviated identifiers.

### 1.4 Exception Handling
```
try:
    ...
except:
    ui.messageBox(traceback.format_exc())
```

### 1.5 Unit Safety
- Always use `ValueInput`.
- Never rely on user unit settings.

---

## 2. Add-In Folder Structure Rules

### 2.1 Required Layout
```
MyAddIn/
    MyAddIn.py
    MyAddIn.manifest
    Modules/
        EA_Main.py
        EA_Geometry.py
        EA_State.py
        EA_UI.py
        EA_Preview.py
```

### 2.2 Manifest Rules
- Must use JSON format.
- Must match folder and entry file name.
- Required:
  - autodeskProduct  
  - type  
  - id  
  - version  
  - author  
  - description  

### 2.3 Version Sync
- Parent folder version matches manifest version.
- Use semantic versioning.

---

## 3. EA Project Rules

### Sketch Export
- LineID starts at 1.
- Export start/end XYZ and length.
- No area calculations unless asked.

### CSV Rules
- Use commas.
- Always include headers.

### Geometry Rules
- Always create bodies in new components.
- Use construction geometry for stability.
- Use named parameters.

### Preview Rules
- Use temp BRep.
- Delete preview entities when done.

---

## 4. UI & Event Rules

### Required Command Methods
- onCreate  
- onExecute  
- onInputChanged  
- onDestroy  

### Events
- Store handlers in global arrays.
- Release all handlers onDestroy.

### UI Panels
- Use “Utilities” workspace by default.

---

## 5. State Management Rules

### `EA_State.py`
- Central location for persistent values.
- Use getters/setters.
- No state logic inside UI or geometry modules.

### Globals
- Only app/ui references + handler arrays.

---

## 6. Coding Style Rules

- Explicit casting only (float, int).
- Consistent debugging practices.
- Use small, readable functions.
- Comment geometry steps clearly.

---

## 7. Safety & Error Proofing

- Validate sketches, bodies, extrusions.
- Handle empty selection sets.
- Clean up temporary geometry.
- Avoid referencing timeline indices.

---

## 8. GitHub Workflow

- Keep each add-in version in a separate folder.
- Maintain `CHANGELOG.md`.
- Main branch must always be runnable.
- Always load the rules file before coding sessions.

---

## 9. ChatGPT Collaboration

- Generate ONE complete script per module.
- Use safe delivery mode (small file batches).
- Avoid ZIP output unless explicitly requested.
- Ask for clarification if geometry intent is unclear.

---

## 10. Future-Proofing

- Avoid deprecated API calls.
- Maintain modular code.
- Prefer named construction geometry.
- Avoid direct face references.

---

End of File
