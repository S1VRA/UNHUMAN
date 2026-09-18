# Architecture

## Overview

NH Mod Tool is a Python desktop application built with CustomTkinter. It manages mods and photo packs for Need for Heat on Windows.

## Core Files

### `NHModTool.py` (2300+ lines)

The main application file. Contains all UI logic, event handling, file operations, mod management, and game detection. Uses CustomTkinter widgets throughout.

### `theme.py`

Defines the Obsidian dark theme. Exports color palettes, font configurations, and CustomTkinter theme settings applied at application startup.

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

- `build.spec` — PyInstaller spec file for building the `.exe`
- Helper scripts for packaging

## Data Flow

```
User Input → NHModTool.py → File System (data/, mods/)
                              → i18n.py → locales/
                              → theme.py → CustomTkinter
```

## Dependencies

| Package          | Purpose                      |
|------------------|------------------------------|
| customtkinter    | Modern tkinter UI framework  |
| Pillow           | Image processing             |
| zipfile          | ZIP archive handling (stdlib)|
| shutil           | File operations (stdlib)     |
| json             | Configuration storage (stdlib)|
