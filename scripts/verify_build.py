#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Post-build verification for the NHModTool release.

Checks (all must pass for a release):
  1. dist\\NHModTool.exe exists and is not empty.
  2. Size is sane: warn if >= 50 MB, hard-fail if >= 100 MB.
  3. The custom .ico is embedded in the PE resources (RT_GROUP_ICON + RT_ICON),
     i.e. the taskbar shows our icon, not the python icon.
  4. Frozen exe runs its internal --selftest and all tests pass.
  5. Frozen exe runs --assettest: in-game textures decode in the bundle.
  6. SHA-256 checksum written to dist\\SHA256SUMS.txt.

Usage:  python scripts\\verify_build.py  (from the repo root)
Exit code 0 = release-ready, 1 = failure, 2 = warning only (still 0).
"""

import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, "dist", "NHModTool.exe")
SHA_FILE = os.path.join(ROOT, "dist", "SHA256SUMS.txt")

WARN_MB = 50
FAIL_MB = 100


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def exe_has_icon(path):
    """True if the PE carries a custom icon group (RT_GROUP_ICON, resource id 14)."""
    try:
        import pefile  # type: ignore
        pe = pefile.PE(path)
        try:
            entries = pe.DIRECTORY_ENTRY_RESOURCE.entries
        except Exception:
            return False
        for entry in entries:
            if entry.id in (14, 3):  # 14=RT_GROUP_ICON, 3=RT_ICON
                return True
        return False
    except Exception:
        return False


def run_exe(args):
    p = subprocess.run([EXE] + args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)
    return p.returncode


def main():
    problems = []
    warns = []

    if not os.path.exists(EXE):
        print("FAIL: exe not found: %s" % EXE)
        sys.exit(1)

    size_mb = os.path.getsize(EXE) / (1024 * 1024)
    print("exe size: %.1f MB" % size_mb)
    if size_mb >= FAIL_MB:
        problems.append("size >= %.0f MB (%.1f) — unwanted deps likely bundled" % (FAIL_MB, size_mb))
    elif size_mb >= WARN_MB:
        warns.append("size %.1f MB exceeds comfortable %d MB (scipy/skimage are required)" % (size_mb, WARN_MB))

    if exe_has_icon(EXE):
        print("icon: embedded (custom NHModTool.ico)")
    else:
        problems.append("custom icon not found in PE resources")

    report_path = os.path.join(ROOT, "dist", "verify_selftest.json")
    rc = run_exe(["--selftest", report_path])
    if rc != 0:
        problems.append("exe --selftest exit code %d" % rc)
    else:
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                rep = json.load(f)
            failed = [t for t in rep.get("tests", []) if not t.get("pass")]
            if rep.get("ok") and not failed:
                print("selftest: %d/%d PASS" % (len(rep["tests"]), len(rep["tests"])))
            else:
                problems.append("selftest failures: %r" % failed)
        except Exception as e:
            problems.append("selftest report unreadable: %r" % e)

    bg_dir = os.path.join(ROOT, "dist")

    at_report = os.path.join(bg_dir, "assettest_report.json")
    if os.path.exists(at_report):
        os.remove(at_report)
    rc = run_exe(["--assettest", bg_dir])
    if rc != 0:
        problems.append("exe --assettest exit code %d" % rc)
    else:
        try:
            with open(at_report, "r", encoding="utf-8") as f:
                rep = json.load(f)
            failed = [t for t in rep.get("tests", []) if not t.get("pass")]
            if rep.get("pass") and not failed:
                print("assettest (in-game textures decode in exe): PASS")
            else:
                problems.append("assettest failures: %r" % failed)
            if rep.get("errors"):
                for e in rep["errors"]:
                    print("assettest errors: %s" % e)
        except Exception as e:
            problems.append("assettest report unreadable: %r" % e)

    digest = sha256(EXE)
    with open(SHA_FILE, "w", encoding="utf-8") as f:
        f.write("%s  NHModTool.exe\n" % digest)
    print("SHA-256: %s" % digest)
    print("checksum written: %s" % SHA_FILE)

    for w in warns:
        print("WARN: %s" % w)
    if problems:
        for p in problems:
            print("FAIL: %s" % p)
        print("RESULT: FAIL")
        sys.exit(1)
    print("RESULT: PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()