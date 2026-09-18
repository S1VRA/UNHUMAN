# -*- coding: utf-8 -*-
"""Optional release-artifact checks. Skipped when dist\\NHModTool.exe is absent."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, "dist", "NHModTool.exe")


@unittest.skipUnless(os.path.exists(EXE), "dist\\NHModTool.exe not built")
class PackagingTest(unittest.TestCase):
    def test_exe_exists_and_reasonable_size(self):
        size_mb = os.path.getsize(EXE) / (1024 * 1024)
        self.assertGreater(size_mb, 20, "exe suspiciously small")
        self.assertLess(size_mb, 300, "unwanted deps (torch?) re-bundled %.1f MB" % size_mb)

    def test_checksum_file_with_exe_checksum(self):
        sha_path = os.path.join(ROOT, "dist", "SHA256SUMS.txt")
        self.assertTrue(os.path.isfile(sha_path), "dist\\SHA256SUMS.txt missing")
        with open(sha_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("NHModTool.exe", content)
        digest = content.split()[0]
        self.assertEqual(len(digest), 64)

    def test_version_info_source_is_present(self):
        self.assertTrue(os.path.isfile(os.path.join(ROOT, "version_info.txt")))

    def test_spec_bundles_unitypy_runtime_resources(self):
        spec = os.path.join(ROOT, "NHModTool.spec")
        self.assertTrue(os.path.isfile(spec), "NHModTool.spec missing")
        with open(spec, "r", encoding="utf-8") as f:
            content = f.read()
        # UnityPy loads its type-tree DB via importlib.resources ("UnityPy.resources")
        # and fmod_toolkit's native dll via an env-var path; neither is visible to
        # PyInstaller static analysis, so they MUST be collected explicitly or the
        # frozen gallery shows zero thumbnails.
        self.assertIn("collect_data_files('UnityPy')", content)
        self.assertIn("hiddenimports=['UnityPy.resources', 'archspec', 'archspec.cpu']", content)
        self.assertIn("collect_data_files('fmod_toolkit')", content)

    def test_real_game_file_untouched(self):
        real = r"C:\Users\mehmet\AppData\Games\No, I'm not a Human" \
               r"\NoImNotAHuman_Data\sharedassets0.assets"
        if not os.path.exists(real):
            self.skipTest("game not installed on this machine")
        import NHModTool as app
        known = "d6f95496f611da8d34969a064fb13696"
        self.assertEqual(app.file_md5(real), known,
                         "REAL GAME FILE WAS MODIFIED - restore from backup!")


if __name__ == "__main__":
    unittest.main()