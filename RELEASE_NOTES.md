# NH Mod Tool v0.5.0

**Release Date:** 2026-09-26

## Highlights

- Modern dark UI (ttkbootstrap / darkly theme)
- Full Turkish localization
- Security hardening (ZIP Slip, ZIP bomb, path traversal)
- Professional Windows installer (Inno Setup)

## What's New

### Added
- Settings schema validation for `settings.json`
- Managed-root safety gate for recursive delete operations
- Centralized logging under `%APPDATA%\NHModTool\logs`
- Global exception handlers (sys, threading, Tk callbacks)
- UI modernization: Primary/Secondary/Danger/Ghost button categories, focus rings, empty-state screens, DPI awareness, persisted window position/size, responsive grid layout
- Single source of truth for theming via `theme.py`
- Turkish localization (full EN/TR parity)
- Windows Installer via Inno Setup
- Nuitka standalone build (replaces PyInstaller)

### Changed
- Migrated from custom ttk themes to ttkbootstrap (darkly theme)
- All user-facing strings moved to locale files (EN/TR) with strict key and placeholder parity; no hardcoded UI text left in the source
- UI layer rebuilt around the shared theme module and button taxonomy
- Packaging: Nuitka standalone + Inno Setup installer (replaces PyInstaller)

### Fixed
- ZIP Slip path traversal
- ZIP bomb protection
- Magic-byte validation for assets
- Locale text leakage

### Removed
- Legacy apply_obsidian_theme function
- PyInstaller spec file
- Dead code (shadowed `preview_in_label`, unused `_make_checkerboard`, `DATA_DIR_LOW`)

## Install

Download `NHModTool_v0.5.0_Setup.exe` and run it.

## Known Issues

- Microsoft Defender may show a false positive on the installer. This is a known issue for unsigned Python applications. The source code is fully available.

## Checksums

SHA-256: 3931FCAC6F75208D9AF4E7951A9C90ED9229D67340C7D2CE38A4BCCACB99B64F