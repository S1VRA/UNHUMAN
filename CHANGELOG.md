# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned

- Auto-update mechanism.
- Additional language packs (German, Spanish, French).
- Linux and macOS support.
- Theme customization options.
- Screenshots in README.

---

## [0.5.0] - 2026-09-26

### Added

- Settings schema validation for `settings.json`.
- Managed-root safety gate for recursive delete (`rmtree`) operations.
- Centralized logging under `%APPDATA%\NHModTool\logs` with a
  `RotatingFileHandler`, plus a global exception handler covering
  `sys` hooks, threading, and Tk callbacks.
- UI modernization: Primary/Secondary/Danger/Ghost button categories,
  focus rings, empty-state screens, DPI awareness, persisted window
  position/size, and a responsive grid layout.
- Single source of truth for theming via `theme.py`.
- Turkish localization (full EN/TR parity).
- Windows Installer via Inno Setup (replaces zip distribution).
- Nuitka standalone build (replaces PyInstaller).
- Settings schema validation for `settings.json`.
- Managed-root safety gate for recursive delete operations.
- Centralized logging under `%APPDATA%\NHModTool\logs`.
- Global exception handlers (sys, threading, Tk callbacks).

### Changed

- Migrated from custom ttk themes to ttkbootstrap (darkly theme).
- All user-facing strings moved to locale files (EN/TR) with strict key
  and placeholder parity; no hardcoded UI text left in the source.
- UI layer rebuilt around the shared theme module and button taxonomy.
- Packaging: Nuitka standalone + Inno Setup installer (replaces PyInstaller).

### Fixed

- ZIP Slip path traversal blocked during photo-pack extraction.
- ZIP bomb protection (size/ratio limits) during import.
- Magic-byte validation for assets and ZIP imports.
- Turkish/English UI text no longer leaks into the other locale.
- ZIP Slip path traversal.
- ZIP bomb protection.
- Magic-byte validation for assets.
- Locale text leakage.

### Removed

- Legacy apply_obsidian_theme function.
- PyInstaller spec file.
- Dead code (shadowed `preview_in_label`, unused `_make_checkerboard`, `DATA_DIR_LOW`).

---

## [0.4.0] - 2026-09-18

### Added

- Full internationalization (i18n) with English and Turkish locales.
- Obsidian dark theme applied via tkinter/ttk theming.
- Photo Pack ZIP import with extraction, validation, and progress feedback.
- Mod Manager with install, uninstall, enable, and disable actions.
- Game status panel with real-time process detection.
- Documentation: INSTALL.md, USAGE.md, ARCHITECTURE.md.
- GitHub community files: CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md.
- GitHub issue templates and pull request template.
- GitHub Actions CI workflow.
- AI-generated project banner (`assets/banner.png`).

### Fixed

- Empty UI on first launch (App class was not instantiated).
- Removed invalid `_add_hover_effect` calls on ttk.Button widgets
  (caused "unknown option '-background'" errors).
- Backup date formatting now uses `os.path.getmtime`.
- Combobox language selection now persists correctly.
- EXE build bundles `locales/` and creates default `settings.json` on first run.
- `except: pass` blocks replaced with proper error logging.

### Changed

- Project restructured: tests → `tests/`, screenshots → `tests/outputs/`,
  backups → `backups/dev/`.
- Legacy `nh_mod_tool_settings.json` replaced by `data/settings.json`.
- `NHModTool.bat` moved to `scripts/`.
- `AUDIT.md` moved to `docs/`.
- README rewritten as bilingual (EN/TR).

---

## [0.3.0] - 2026-09-16

### Added

- Initial public release.
- Core mod management UI with tkinter/ttk.
- Basic photo pack browsing and installation.
- Settings panel for directory configuration.