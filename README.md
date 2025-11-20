# Fusion 360 Add-In Development Rules — Documentation Set

This repository contains authoritative rules, coding standards, and workflows for developing stable, modular, and scalable Fusion 360 add-ins.  
These rules are designed to support long-term projects, versioned development, and collaboration with ChatGPT.

---

## 📘 Purpose of This Repository

The goal of this documentation set is to:

- Provide a **single source of truth** for Fusion 360 add-in standards.
- Ensure **consistent quality and structure** across all versions.
- Enable **clean iterative improvement** over time.
- Allow ChatGPT to reference a stable ruleset before each session.

---

## 📄 What’s Included

### ✔ `Fusion360_AddIn_Rules_v1_0_0.txt`
The full, formalized ruleset:
- Folder structure  
- Manifest rules  
- Geometry conventions  
- CSV/export rules  
- UI & event structure  
- State management  
- Error-proofing  
- GitHub workflow  
- ChatGPT collaboration rules  

### ✔ `Fusion360_AddIn_Rules_v1_0_0.md`
Markdown-formatted GitHub-friendly rules.

### ✔ `CHANGELOG.md`
Tracks all additions, changes, and fixes across versions.

---

## 🔧 How to Use These Rules

### 1. **For GitHub Projects**
Include the latest version in your repository root, for example:

```
/docs/
    Fusion360_AddIn_Rules_v1_0_0.md
    CHANGELOG.md
```

### 2. **For ChatGPT Sessions**
Before starting new Fusion 360 scripting or add-in development chats:

Tell ChatGPT:
> “Reference the GitHub rules file before generating code.”

This ensures:
- Consistent coding styles  
- Correct Fusion 360 structure  
- Stable, reusable patterns  
- No regression from previous work  

### 3. **For Versioning**
Use semantic versioning:

- **MAJOR** → structural or breaking changes  
- **MINOR** → new rules/features added  
- **PATCH** → small corrections or clarifications  

Example:
```
v1.0.0  → Initial release  
v1.1.0  → New geometry rules added  
v1.1.1  → Clarified event handler cleanup  
```

---

## 🧩 Future Updates

As your Fusion 360 project grows, new add-in modules or rules will be added here.  
Each update will:
- Follow versioning conventions  
- Add to `CHANGELOG.md`  
- Include updated `.txt` and `.md` rules files  

---

## 🛠 Need More Help?

Ask ChatGPT:
> “Update the rules to version X.Y.Z.”

and it will:
- Generate updated TXT and MD versions  
- Add CHANGELOG entries  
- Maintain consistent structure  

---

## End of README  
