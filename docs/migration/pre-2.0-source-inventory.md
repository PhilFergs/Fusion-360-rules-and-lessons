# Pre-2.0 Source Inventory

## Verified Rollback

- Rollback root: `C:\Users\phil9\Documents\PhilsFusionTools-Rollback\20260730-111056`
- Manifest SHA-256: `898b56dac144dbc432e46babe364654e66750377e9bee99e4cdce2aa9eae4223`
- Source commit at capture: `6903040ac614d64d5bf798e2610f80cd159951e6`
- Source branch at capture: `feature/in-development`
- Dirty status entries at capture: `105`
- Untracked files archived: `116`

The rollback verifier passed archive SHA-256 checks, ZIP integrity tests, and Git bundle verification. The restore script passed in dry-run mode without changing any Fusion or source files.

## Intended Tracked Changes Carried Forward

- `Addin/CHANGELOG.md`
- `Addin/DEVLOG.md`
- `Addin/PhilsDesignTools/PhilsDesignTools.py`
- `Addin/PhilsDesignTools/smg_core.py`
- `Addin/README.md`
- `tasks/todo.md`

## Intended Local-Only Source Carried Forward

- `Addin/PhilsDesignTools/smg_c_channel.py`
- `Addin/PhilsDesignTools/smg_ibeam.py`
- `Addin/PhilsDesignTools/smg_pfc.py`
- `Addin/PhilsDesignTools/resources/PhilsDesignTools_CChannel/16x16.png`
- `Addin/PhilsDesignTools/resources/PhilsDesignTools_CChannel/32x32.png`
- `Addin/PhilsDesignTools/resources/PhilsDesignTools_IBeam/16x16.png`
- `Addin/PhilsDesignTools/resources/PhilsDesignTools_IBeam/32x32.png`
- `Addin/PhilsDesignTools/resources/PhilsDesignTools_PFC/16x16.png`
- `Addin/PhilsDesignTools/resources/PhilsDesignTools_PFC/32x32.png`

## Intentionally Excluded From The 2.0 Worktree

The verified rollback retains these files, but they are not carried into the implementation branch:

- Timestamped `.bak-*` files.
- Python bytecode and `__pycache__`.
- Runtime logs.
- Installer `_build` intermediates.
- Historical `Addin/tools/dist` packages.
- Visual-companion session files.

## Installed Reference Hashes

These hashes identify the active files at rollback capture:

| File | SHA-256 |
|---|---|
| Active BOM `_PhilsBom.py` | `06a226ff682a7752f6bfb424d283c1dabc95dd379a9bc8dd55ba68f4124168b8` |
| Active BOM `PackageContents.xml` | `67aba238b7a9bec36ad6034eef531e7dfa10708f8334b86e8eba9836e7cd2c2a` |
| Active Design Tools `PhilsDesignTools.py` | `0182e14021c769b25c63f9645e8f0496248d8e766f13e55db1eef6b5cee08309` |
| Active Design Tools manifest | `35c27ade58839ca1e86ffab50b92e2cca068e07321bb27548f7f7723632dd81d` |

The complete installed folders, settings, logs, source tree, Git history, tracked patch, and untracked files are preserved in the rollback set. These four hashes are quick reference identifiers, not substitutes for the complete archive manifest.
