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