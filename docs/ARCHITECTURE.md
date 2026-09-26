# Architecture

## Overview

NH Mod Tool is a Python desktop application built with **ttkbootstrap (darkly theme)**. It manages mods and photo packs for "No, I'm not a Human" on Windows.

## Core Files

### `NHModTool.py` (~3600 lines)

The main application file. Contains all UI logic, event handling, file operations, mod management, and game detection. Uses ttkbootstrap widgets throughout.

### `theme.py`

Defines the theme tokens (PALETTE, TYPOGRAPHY, SPACING). Single source of truth for theming. Exports color palettes, font configurations, and spacing tokens applied at application startup.

### `i18n.py`

Localization engine. Loads translation files from `locales/` and provides a `gettext`-style interface for string lookups throughout the UI.

### `locales/`

Directory containing translation files:

- `en.json` — English translations
- `tr.json` — Turkish translations

### `data/`

Runtime directory for user-specific data:

- Installed mod registry
- Backup archives
- User preferences (JSON)

### `scripts/`

Build and development helpers:

- `build_release.bat` — Nuitka build script
- Helper scripts for packaging

## Data Flow

```
User Input → NHModTool.py → File System (data/, mods/)
                          → i18n.py → locales/
                          → theme.py → ttkbootstrap
```

## Dependencies

| Package          | Purpose                              |
|------------------|--------------------------------------|
| ttkbootstrap     | Modern tkinter UI framework (darkly) |
| Pillow           | Image processing                     |
| zipfile          | ZIP archive handling (stdlib)        |
| shutil           | File operations (stdlib)             |
| json             | Configuration storage (stdlib)       |
| UnityPy          | Unity asset bundle handling          |
| zstandard        | Compression                          |

## Version 0.5.0 Architecture Notes

- **Monolith structure**: Single `NHModTool.py` (~3600 lines) with all UI logic, event handling, file operations, mod management, and game detection
- **theme.py**: Single source of truth for PALETTE, TYPOGRAPHY, SPACING tokens
- **i18n.py**: `t(key)` gettext-style engine with EN/TR locale files
- **Packaging**: Nuitka standalone (folder mode) + Inno Setup installer
- **Theme**: ttkbootstrap darkly theme with custom PALETTE token overrides
- **i18n**: Full EN/TR parity with strict key/placeholder parity
- **Packaging**: Nuitka standalone (folder mode) + Inno Setup installer (replaces PyInstaller + zip distribution)