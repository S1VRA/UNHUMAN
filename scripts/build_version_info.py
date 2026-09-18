# -*- mode: python ; coding: utf-8 -*-
"""Generates PyInstaller version resource file (version_info.txt).

Run:  python -m PyInstaller --version-file scripts/version_info.txt NHModTool.spec
or from build_release.bat.
"""

APP_NAME = "NHModTool"
APP_DISPLAY_NAME = "NH Mod Tool"
APP_DESCRIPTION = "No I'm Not A Human - Photo Mod injector / texture switcher"
APP_COMPANY = "S1VRA"
APP_COPYRIGHT = "Copyright (c) 2026 S1VRA"
APP_VERSION = "0.4.0"

# PyInstaller requires the version list to be passed via pyi_versioninfo
from PyInstaller.utils.win32 import versioninfo  # noqa: E402

vs = versioninfo.VSVersionInfo(
    ffi=versioninfo.FixedFileInfo(
        filevers=(0, 4, 0, 0),
        prodvers=(0, 4, 0, 0),
        mask=0x3F,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0),
    ),
    kids=[
        versioninfo.StringFileInfo(
            [
                versioninfo.StringTable(
                    "040904B0",
                    [
                        versioninfo.StringStruct("CompanyName", APP_COMPANY),
                        versioninfo.StringStruct("FileDescription", APP_DESCRIPTION),
                        versioninfo.StringStruct("FileVersion", APP_VERSION),
                        versioninfo.StringStruct("InternalName", APP_NAME),
                        versioninfo.StringStruct("LegalCopyright", APP_COPYRIGHT),
                        versioninfo.StringStruct(
                            "OriginalFilename", APP_NAME + ".exe"
                        ),
                        versioninfo.StringStruct("ProductName", APP_DISPLAY_NAME),
                        versioninfo.StringStruct("ProductVersion", APP_VERSION),
                    ],
                )
            ]
        ),
        versioninfo.VarFileInfo(
            [versioninfo.VarStruct("Translation", [1033, 1200])]
        ),
    ],
)

with open("version_info.txt", "w", encoding="utf-8") as f:
    f.write(str(vs))

print("Wrote version_info.txt (version %s)" % APP_VERSION)