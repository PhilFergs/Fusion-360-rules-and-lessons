# Phils Design Tools workflow guide

This document captures the current workflow and the planned automation steps
for moving from wireframe to fabrication-ready steel models.

## Source input
- Wireframe DXF from Rhino, with all members in their generic positions.
- Wireframes are separated by sector and member types using layer names.
- Sector names are user-defined at import time.

## Workflow map
1. Locate steel wireframe model.
2. Import wireframe into Fusion 360.
3. Generate RHS/SHS columns and side arms sector by sector.
4. Trim member ends for brackets (thickness + 3 mm clearance).
5. Place bracket components from the Fusion library.
6. Project bracket outlines to create EA sketch lines.
7. Generate EA members for top brackets; rotate to correct orientation.
8. Create cross-bracing sketches (typically flat to a face).
9. Generate EA cross-bracing; reorient and offset to face.
10. Cut bolt holes.
11. Rename all components per naming convention.
12. Repeat for remaining sectors.
13. Full design check (alignment, holes, naming).
14. Export IGES for RHS/SHS components.
15. Export EA hole list for manufacturing.

## Automation plan (milestones)
1. Import + structure
   - DXF import helper.
   - Create parent components per sector.
2. Generation + orientation
   - Batch RHS/SHS generation by selection or layer.
   - Rotation presets: 0/90/180/270 degrees.
3. Bracket prep + placement
   - Trim end tool (select which end to trim).
   - Bracket placement and alignment.
4. EA from bracket projections
   - Auto projection of bracket footprints to sketch lines.
5. Cross bracing
   - EA generation with offset-to-face helper.
6. Holes + naming
   - Bracket hole cuts through closest RHS/SHS member.
   - EA hole cuts through closest member (EA or RHS/SHS).
   - Naming convention implementation.
7. QA + exports
   - Validation checklist tooling.
   - IGES export for RHS/SHS.
   - EA hole schedule export.

## Key decisions and rules
- Sector identification: layer names in DXF.
- Sector names: user-defined per import.
- Rotation presets: 0/90/180/270 only.
- Trim control: user selects which end to trim.
- Bracket source: Fusion library components.
- Bracket alignment target: bottom face (away from added plates),
  centered between the vertical plates.
- Hole cutting:
  - Bracket holes: offset from bracket hole centers through the closest RHS/SHS.
  - EA holes: through the closest member (EA or RHS/SHS).

## Naming convention
Format: `{SectorLetter}-{TypeWithIndex}-{Size}-{Length}mm`

Examples:
- `P-C1-100x50x3-2400mm`
- `I-CA2-100x50x3-1800mm`
- `S-EAH5-50x50x3-600mm`

TypeWithIndex examples:
- `C1` = column
- `CA1` = column arm
- `EAH1` = horizontal EA
- `EAB1` = brace EA

## Versioning and deployment
1. Update `CHANGELOG.md` (user-facing) and `DEVLOG.md` (internal notes).
2. Add a dated entry to `VERSION_LOG.md` for each upload.
3. Deploy via `tools/deploy_addin.ps1` to back up the previous add-in folder
   before overwriting the active Fusion add-ins copy.
4. Optional: run `tools/watch_deploy.ps1` during development to auto-copy changes.
