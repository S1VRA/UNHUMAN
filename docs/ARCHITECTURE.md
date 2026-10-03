# Architecture

## Overview

NH Mod Tool is a Python desktop application built with **ttkbootstrap (darkly
theme)**. It manages mods and photo packs for "No, I'm not a Human" on
Windows.

## Core Files

### `NHModTool.py` (3,623 lines)

The main application file: all UI logic, event handling, file operations, mod
management, texture injection and game detection. Uses ttkbootstrap widgets
throughout.

### `theme.py`

Theme tokens (`PALETTE`, `TYPOGRAPHY`, `SPACING`, `RADIUS`). Single source of
truth for theming; applied at application startup.

### `i18n.py`

Localization engine. Loads `locales/<lang>.json` and exposes a `gettext`-style
`t(key, **kwargs)` interface. Missing keys fall back to the key itself.

### `locales/`

- `en.json` — English strings
- `tr.json` — Turkish strings (full key and placeholder parity)

### `data/` (source runs) / `%APPDATA%\NHModTool` (installer)

| Path | Contents |
|------|----------|
| `settings.json` | Game file path, photo directory, language, zoom |
| `backups/` | Timestamped manual backups of the game file |
| `cache/` | Generated thumbnail cache |
| `mod_history.json` | Applied-mod log |
| `logs/app.log` | Rotating application log (1 MB × 2 backups) |

When frozen, the tool never writes beside the executable (Program Files is
read-only), so user data is redirected to `%APPDATA%\NHModTool`.

### `scripts/`

| File | Purpose |
|------|---------|
| `build_version_info.py` | Generates `version_info.txt` for the Windows resource metadata |
| `verify_build.py` | Post-build checks (icon, `--selftest`, `--assettest`, SHA-256) |
| `NHModTool.bat` | Convenience launcher |

`build_release.bat` (Nuitka build) lives in the **repository root**, together
with `installer.iss` (Inno Setup).

## Data Flow

```
User Input
   │
   ▼
NHModTool.py ──► i18n.py ──► locales/{en,tr}.json
   │
   ├──► theme.py ──► ttkbootstrap (darkly)
   │
   └──► UnityPy ──► sharedassets0.assets  (read → modify → verify → atomic replace)
                        │
                        └──► sharedassets0.assets.bak  (automatic original backup)
```

## Texture Write Pipeline

This is the part most likely to need debugging, so it is worth spelling out:

| Step | Function | Notes |
|------|----------|-------|
| 1 | `pick_photo` / `_collect_zip_images` | Source is converted to RGBA on load, so transparency survives. |
| 2 | `_prep_sheet` | Scales the photo to fit the texture's own pixel size and centres it on a transparent RGBA canvas. Pasted **without** a mask so alpha is copied verbatim. |
| 3 | `_format_keeps_alpha` | Reports whether the target Unity texture format can store alpha at all. |
| 4 | `Texture2D.set_image` | Re-encodes via UnityPy at the texture's **original** format and mipmap count. |
| 5 | `_verify_objects` | Re-reads the dump and aborts unless exactly the intended `Texture2D` changed. |
| 6 | `_commit_modified` | Creates the `.bak` if missing, then `os.replace`s the file atomically. |

Alpha-capable target formats used by this title: **DXT5**, **DXT5Crunched**,
**RGBA32**. Formats without alpha (**DXT1**, **ETC_RGB\***, **ATC_RGB\***,
**ASTC_RGB\***, **RGB24**, **PVRTC_RGB\***) flatten transparency; step 3 logs a
warning when that happens.

## Dependencies

Declared in `requirements.txt`:

| Package | Purpose |
|---------|---------|
| UnityPy | Unity asset bundle reading and texture encoding |
| Pillow | Image processing |
| ttkbootstrap | Modern tkinter UI framework (darkly) |
| zstandard | Compression |
| nuitka / ordered-set | Build-time only |

Pulled in transitively by UnityPy and used on the texture path:

| Package | Purpose |
|---------|---------|
| etcpak | BCn / ETC block compression — **required to write** DXT1/DXT5/BC/ETC textures |
| texture2ddecoder | Block decompression — required to read them back |
| astc-encoder-py | ASTC codec (excluded from the build; this title ships no ASTC textures) |
| lz4, brotli, fsspec, tpk_ar | Bundle decompression helpers |
| fmod_toolkit | Audio bank parsing shipped by UnityPy |

Standard library modules used directly include `zipfile`, `shutil`, `json`,
`logging`, `hashlib` and `gc`.

## Version 0.5.0 Architecture Notes

- **Monolith structure** — a single `NHModTool.py` holding UI, events, file
  operations, mod management and game detection.
- **theme.py** — single source of truth for `PALETTE`, `TYPOGRAPHY`, `SPACING`
  and `RADIUS` tokens.
- **i18n.py** — `t(key)` engine with EN/TR locale files and strict
  key/placeholder parity.
- **Packaging** — Nuitka standalone (folder mode) + Inno Setup installer,
  replacing the old PyInstaller + ZIP distribution.
- **astc_encoder excluded** — the game ships no ASTC textures (observed
  formats are RGBA32 and DXT5), so `astc_exclude.yml` strips UnityPy's
  top-level `astc_encoder` import. This also avoids an AVX2 instruction fault
  on older CPUs.
