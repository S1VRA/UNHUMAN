# -*- coding: utf-8 -*-
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import NHModTool as app  # noqa: E402


class FileSafetyTest(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp(prefix="nh_safety_")

    def _write(self, path, data):
        with io.open(path, "wb") as f:
            f.write(data)

    def test_atomic_replace_replaces_content(self):
        src = os.path.join(self.tmp, "src.bin")
        dst = os.path.join(self.tmp, "dst.bin")
        self._write(src, b"new-content")
        app._atomic_replace(src, dst)
        with io.open(dst, "rb") as f:
            self.assertEqual(f.read(), b"new-content")

    def test_atomic_replace_cleans_temp(self):
        src = os.path.join(self.tmp, "src2.bin")
        dst = os.path.join(self.tmp, "dst2.bin")
        self._write(src, b"x" * 100)
        app._atomic_replace(src, dst)
        self.assertFalse(os.path.exists(dst + ".tmp"))

    def test_atomic_replace_overwrites_existing(self):
        src = os.path.join(self.tmp, "src3.bin")
        dst = os.path.join(self.tmp, "dst3.bin")
        self._write(dst, b"old")
        self._write(src, b"new")
        app._atomic_replace(src, dst)
        with io.open(dst, "rb") as f:
            self.assertEqual(f.read(), b"new")

    def test_atomic_replace_into_subdir(self):
        sub = os.path.join(self.tmp, "sub")
        os.makedirs(sub)
        src = os.path.join(self.tmp, "src4.bin")
        dst = os.path.join(sub, "dst4.bin")
        self._write(src, b"deep")
        app._atomic_replace(src, dst)
        self.assertTrue(os.path.isfile(dst))

    def test_file_md5_is_stable(self):
        p = os.path.join(self.tmp, "hash.bin")
        p2 = os.path.join(self.tmp, "hash2.bin")
        self._write(p, b"hashme")
        self._write(p2, b"hashme-bis")
        self.assertEqual(app.file_md5(p), app.file_md5(p))
        self.assertNotEqual(app.file_md5(p), app.file_md5(p2))

    def test_ensure_free_space_rejects_huge_request(self):
        with self.assertRaises(IOError):
            app._ensure_free_space(self.tmp, 1 << 40)

    def test_ensure_free_space_passes_small_request(self):
        app._ensure_free_space(self.tmp, 4096)  # should not raise


class BackupRestoreCycleTest(unittest.TestCase):
    """Full backup -> modify -> restore cycle on a FAKE game file.

    Mirrors the app's real commit/restore flow (_atomic_replace) while a
    checksum proves the file is byte-identical after restore.
    """

    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp(prefix="nh_cycle_")
        self.game_dir = os.path.join(self.tmp, "NoImNotAHuman_Data")
        os.makedirs(self.game_dir)
        self.game = os.path.join(self.game_dir, app.ASSETS_NAME)
        self.original = b"GAME_ASSET_HEADER" + b"\x00" * 2048 + b"END"
        with io.open(self.game, "wb") as f:
            f.write(self.original)
        self.orig_md5 = app.file_md5(self.game)
        self.backup = os.path.join(self.tmp, "backup.assets")

    def test_cycle_restores_byte_identical_file(self):
        # 1) backup
        import shutil
        shutil.copy2(self.game, self.backup)
        # 2) modify (simulated application)
        modified = self.original[:-3] + b"MOD"
        mod_src = os.path.join(self.tmp, "modified.bin")
        with io.open(mod_src, "wb") as f:
            f.write(modified)
        app._atomic_replace(mod_src, self.game)
        self.assertNotEqual(self.orig_md5, app.file_md5(self.game))
        # 3) restore
        app._atomic_replace(self.backup, self.game)
        self.assertEqual(self.orig_md5, app.file_md5(self.game))
        with io.open(self.game, "rb") as f:
            self.assertEqual(f.read(), self.original)
        # 4) no stray temp file left behind
        self.assertFalse(os.path.exists(self.game + ".tmp"))


if __name__ == "__main__":
    unittest.main()