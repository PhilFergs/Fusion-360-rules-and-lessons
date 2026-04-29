# Fusion 360 Add-ins (Release Packages)

This repo contains release zip packages:

- PhilsDesignTools-1.0.9.zip
  - Steel member generation + utilities (EA/SHS/RHS, rotate, rename, hole cut, stub arms, exports).
- PhilsBom.bundle-1.03.zip
  - BOM export add-in (CSV/XLSX/XML/JSON, unit control, include/exclude options, mass totals).
- fusion360-addins-installer-pdt-1.0.9-bom-1.03.zip
  - One-click installer package for both add-ins (PhilsDesignTools + PhilsBom.bundle) with overwrite support.
- fusion360-addins-installer-pdt-1.0.9-bom-1.03.msi
  - Windows MSI wrapper that runs the packaged Fusion add-ins installer for both add-ins.

Package notes:
- `PhilsDesignTools-*.zip` and `PhilsBom.bundle-*.zip` contain add-in folders plus install notes.
- `fusion360-addins-installer-*.zip` contains `Install_Fusion_Addins.cmd` and payload zips for both add-ins.

Install
1) Download and unzip the desired package.
2) For installer package: run `Install_Fusion_Addins.cmd`.
3) For individual add-in zips: open Install_Instructions.txt and follow the steps.
4) Restart Fusion 360 and run the add-in from Tools > Add-ins > Scripts and Add-ins.
