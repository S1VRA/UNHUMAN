# -*- coding: utf-8 -*-
"""PyInstaller runtime hook: install a minimal no-op `numba` shim.

Why:
  rembg/bg.py imports pymatting at module level, and several pymatting
  modules do `from numba import njit, prange` /  `@njit(...)` at import
  time. NHModTool only ever calls `rembg.remove(...)` with default
  settings (alpha_matting=False), so the numba-JIT-ed routines are never
  actually executed - the import alone is what must succeed.

  Bundling the real numba+llvmlite would add ~150 MB to the exe for zero
  runtime benefit, so we instead satisfy the import with a pure-Python
  shim whose decorators are transparent no-ops.

  If a future code path ever enables alpha matting, remove this hook and
  include numba in the PyInstaller excludes list.
"""

import sys


def _noop_decorator(*args, **kwargs):
    if len(args) == 1 and callable(args[0]) and not kwargs:
        return args[0]
    def wrap(func):
        return func
    return wrap


_shim = type(sys)("numba")
_shim.__version__ = "0.0.0-shim"
_shim.njit = _noop_decorator
_shim.jit = _noop_decorator
_shim.vectorize = _noop_decorator
_shim.guvectorize = _noop_decorator
_shim.pndindex = _noop_decorator
_shim.prange = range

_sysmodules = getattr(sys, "modules", {})
if "numba" not in _sysmodules:
    _sysmodules["numba"] = _shim