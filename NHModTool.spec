# -*- mode: python ; coding: utf-8 -*-
#
# NHModTool PyInstaller spec (release build).
# Usage: python -m PyInstaller NHModTool.spec
#
# Notes:
#  - torch/torchvision/torchaudio are excluded.
#  - numba/llvmlite/matplotlib/IPython are not actually executed.
#  - Background removal (rembg) has been removed; no scipy/scikit-image/pymatting/onnxruntime needed.

from PyInstaller.utils.hooks import copy_metadata, collect_data_files, collect_dynamic_libs

_datas = [('NHModTool.ico', '.')]
_datas += [('locales/*.json', 'locales')]
# UnityPy reads its type-tree database (resources/lzma.tpk) through
# importlib.resources.files("UnityPy.resources"), which static analysis misses;
# without it every Texture2D obj.read() raises
# "ModuleNotFoundError: No module named 'UnityPy.resources'" and the character
# gallery comes up empty in the frozen build. Both the package and its data
# file must be added explicitly.
_datas += collect_data_files('UnityPy')
# UnityPy's AudioClipConverter imports fmod_toolkit, which in turn loads its
# native fmod.dll via an env-var path that PyInstaller's analysis cannot see;
# the dll must ship (and live in the same fmod_toolkit/libfmod/Windows/x64/
# location) or object decode raises PyInstallerImportError at runtime.
_datas += collect_data_files('fmod_toolkit')
_datas += collect_dynamic_libs('fmod_toolkit')
# archspec ships cpu/microarchitectures.json read via a path relative to the
# package directory (../json/cpu/...); PyInstaller analysis cannot see it.
_datas += collect_data_files('archspec')


a = Analysis(
    ['NHModTool.py'],
    pathex=[],
    binaries=[],
    datas=_datas,
    hiddenimports=['UnityPy.resources', 'archspec', 'archspec.cpu'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['scripts/runtime_numba_shim.py'],
    excludes=[
        # PyTorch stack
        'torch',
        'torchvision',
        'torchaudio',
        # numba/JIT stack
        'numba',
        'llvmlite',
        # rembg stack (no longer used)
        'rembg',
        'onnxruntime',
        'scipy',
        'skimage',
        'pymatting',
        'cv2',
        # not used at runtime
        'matplotlib',
        'IPython',
        'pytest',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'tkinter.tix',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='NHModTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=True,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['NHModTool.ico'],
    version='version_info.txt',
)