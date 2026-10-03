# Installation Guide

NH Mod Tool ships as a Windows installer. Most users never need Python.

## Prerequisites

### For the installer (recommended)

- **Windows 10/11** (64-bit) — the only supported platform
- Nothing else. Python is **not** required.

### For running from source

- **Python 3.14** or higher — [Download Python](https://www.python.org/downloads/)
- **pip** — included with Python 3.4+
- **Git** — [Download Git](https://git-scm.com/downloads)

---

## Option 1 — Installer (Recommended)

1. Go to the [releases page](https://github.com/S1VRA/UNHUMAN/releases).
2. Download `NHModTool_v0.5.0_Setup.exe`.
3. Run the installer and follow the wizard (English or Turkish).
4. Launch **NH Mod Tool** from the Start Menu.

The installer is created with Inno Setup from `installer.iss` and installs to
`%ProgramFiles%\NH Mod Tool`. It registers an uninstaller, so the app shows up
under **Settings → Apps → Installed apps**.

On first launch the tool scans for the game's `sharedassets0.assets`
(`%LOCALAPPDATA%\Games\No, I'm not a Human\` and your Steam libraries). If it
finds nothing, point it at the file manually via **Settings → Browse…**.

## Option 2 — Run from Source

```bash
git clone https://github.com/S1VRA/UNHUMAN.git
cd UNHUMAN
pip install -r requirements.txt
python NHModTool.py
```

When run from source, user data is written to `./data/` inside the repository
instead of `%APPDATA%\NHModTool`.

---

## Building the Installer (Optional)

Two steps are required. `build_release.bat` only performs the first one.

```bash
# 1) Nuitka standalone build (folder mode) + SHA-256 of the exe
build_release.bat
```

Produces `dist/NHModTool.dist/NHModTool.exe` together with its dependency
folders. This is a standalone *folder* distribution, **not** a single-file
executable.

```bash
# 2) Inno Setup installer (requires Inno Setup 6)
iscc installer.iss
```

Produces `dist/NHModTool_v0.5.0_Setup.exe`.

> Note: PyInstaller is no longer used. It was removed in v0.5.0 along with its
> spec file, because the compiled output triggered antivirus false positives.

---

## Antivirus / SmartScreen

⚠️ **Expect a false positive.**

Some ML-based antivirus engines — including Microsoft Defender — flag the
unsigned installer as malware. This affects **all** unsigned Python-packaged
applications and is not specific to NH Mod Tool.

- **SmartScreen:** *More info* → *Run anyway*.
- **Defender:** allow the file, or verify the SHA-256 published in the release
  notes before allowing it.

The full source code is available for inspection, and you can build the
installer yourself using the steps above.

---

## Troubleshooting

| Symptom | What to do |
|---------|------------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again. |
| `python` is not recognized | Add Python to `PATH` during install, or reinstall with the "Add to PATH" option. |
| Permission denied on `pip install` | Use `pip install --user -r requirements.txt`. |
| Game not detected | **Settings → Browse…** and select `sharedassets0.assets` inside `NoImNotAHuman_Data`. |
| Injection fails | Close the running game and retry — the game file cannot be written while it is open. |
| Character still untextured in game | Restore the backup from **Mod Manager**, then re-apply. |

### Logs

Every run writes a rotating log file:

| Install type | Log location |
|--------------|--------------|
| Installer | `%APPDATA%\NHModTool\logs\app.log` |
| From source | `<repo>\data\logs\app.log` |

The file rotates at 1 MB and keeps two backups (`app.log.1`, `app.log.2`).

For a verbose log, define the `NHMODTOOL_DEBUG` environment variable before
launching the app. Always attach the log file to bug reports.
