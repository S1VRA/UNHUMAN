# Installation Guide

## Prerequisites

- **Python 3.14** or higher — [Download Python](https://www.python.org/downloads/)
- **pip** — Included with Python 3.4+
- **Git** — [Download Git](https://git-scm.com/downloads)
- **Windows 10/11** — Required platform

## Quick Install

```bash
git clone https://github.com/S1VRA/UNHUMAN.git
cd UNHUMAN
pip install -r requirements.txt
```

## Run the Application

```bash
python NHModTool.py
```

## Build Executable (Optional)

To build a standalone `.exe`:

```bash
pip install pyinstaller
pyinstaller scripts/build.spec
```

The executable will be located in the `dist/` directory.

## Troubleshooting

- **ModuleNotFoundError**: Run `pip install -r requirements.txt` again.
- **Python not recognized**: Ensure Python 3.14+ is added to your system PATH.
- **Permission denied**: Run your terminal as administrator or use `--user` flag with pip.
