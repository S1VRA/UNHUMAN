---
name: Bug Report
about: Report a bug to help us improve NH Mod Tool
title: "[Bug] "
labels: bug
assignees: ''
---

## Description

A clear and concise description of what the bug is.

## Steps to Reproduce

1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

## Expected Behavior

A clear and concise description of what you expected to happen.

## Screenshots

If applicable, add screenshots to help explain your problem.

## Environment

- **OS**: Windows 10/11
- **Install type**: Installer / Run from source
- **NH Mod Tool Version**: <fill in — shown in the sidebar footer>
- **Python Version**: 3.14 (source installs only)
- **UnityPy version**: <fill in — first lines of the log file>
- **tkinter Version**: (Python 3.14 built-in)
- **Log file**: attach `%APPDATA%\NHModTool\logs\app.log`
  (or `<repo>\data\logs\app.log` for source installs)

## Photo Details

Fill this in if the bug involves applying a photo.

- **Source image format**: PNG / JPEG / WebP / BMP / GIF
- **Source image has transparency?** yes / no
- **Character name**:
- **Texture format shown on the card**: (e.g. `DXT5`, `RGBA32`, `DXT1`)

> Transparency reference: DXT5, DXT5Crunched and RGBA32 preserve alpha.
> DXT1, ETC_RGB*, ATC_RGB*, ASTC_RGB*, RGB24 and PVRTC_RGB* have no alpha
> channel and flatten it to opaque — the app writes a warning to the log in
> that case, so include that line if you see it.