# VERSION LOG

Each upload should add a dated entry here and use the deploy script to back up
the previous add-in folder before overwriting files in the Fusion add-ins path.

## 2026-04-17 16:45
- Branch: feature/in-development
- Summary: Added Normalize Component Structure, added Stub Arms Export DXF, hardened DXF output for Rhino compatibility (R12/AC1009), and bumped PhilsDesignTools version to 1.0.7.

## 2026-04-20 13:58
- Branch: feature/in-development
- Summary: Added Set Component Descriptions with geometry-only profile/material recognition, hardened SHS/RHS sizing and CHS false-positive handling, refined flat bar vs plate classification, carried forward the Normalize Component Structure naming fix, and bumped PhilsDesignTools version to 1.0.8.

## 2026-03-24 13:20
- Branch: feature/in-development
- Summary: Stub Arms Export upgraded with filetype selection (XLSX default), screws-per-stub-arm setting (default 2), mixed-selection filtering, duplicate line dedupe, and bumped PhilsDesignTools version to 1.0.5.

## 2026-03-30 09:56
- Branch: feature/in-development
- Summary: Upgraded IGES export to Multi Part File Export (STEP/STL/IGES/SAT/SMT/F3D + build-dependent formats), removed length text from generated member names and Batch Rename outputs, and bumped PhilsDesignTools version to 1.0.6.

## 2026-01-22 03:00
- Branch: feature/in-development
- Summary: Stub Arms To Wall overhaul (on-face polygon hits, wall face/body/occurrence selection, column body/occurrence auto face, stub arm lines component, wall clearance with lower-line adjust/drop, no guide lines or wall sketches).

## 2026-02-06 00:00
- Branch: feature/in-development
- Summary: EA From Lines toggle for no-hole members; IGES export selection filters hardened; bumped PhilsDesignTools version to 1.0.1.

## 2026-02-06 00:20
- Branch: feature/in-development
- Summary: Added Sort Components tool (natural sort for child occurrences); bumped PhilsDesignTools version to 1.0.2.

## 2026-02-06 00:35
- Branch: feature/in-development
- Summary: Sort Components can enable design history in Direct mode; bumped PhilsDesignTools version to 1.0.3.

## 2026-02-06 00:50
- Branch: feature/in-development
- Summary: Sort Components safe timeline index handling; bumped PhilsDesignTools version to 1.0.4.

## 2026-01-02 17:05
- Branch: PhilsDesignTools
- Summary: EA rotate axis fix (outer hole face), debug logging, cleanup of unused imports/helper.

## 2026-01-06 20:48
- Branch: PhilsDesignTools
- Summary: Added new commands (EA hole CSV, IGES export, component set, wireframe, hole cut) and moved tools to a dedicated panel.

## 2026-01-16 16:05
- Branch: feature/in-development
- Summary: Added Stub Arms To Wall command with debug logging and updated tool documentation.
