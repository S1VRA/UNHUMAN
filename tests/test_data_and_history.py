# -*- coding: utf-8 -*-
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import NHModTool as app  # noqa: E402


class DataAndHistoryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="nh_hist_")
        self._old = {
            "HISTORY_FILE": app.HISTORY_FILE,
            "SETTINGS_FILE": app.SETTINGS_FILE,
            "DATA_DIR": app.DATA_DIR,
            "CACHE_ROOT": app.CACHE_ROOT,
            "TMP_DIR": app.TMP_DIR,
            "BACKUP_DIR": app.BACKUP_DIR,
            "LOG_DIR": app.LOG_DIR,
        }
        data = os.path.join(self.tmp, "data")
        app.DATA_DIR = data
        app.CACHE_ROOT = os.path.join(data, "cache")
        app.TMP_DIR = os.path.join(data, "tmp")
        app.BACKUP_DIR = os.path.join(data, "backups")
        app.LOG_DIR = os.path.join(data, "logs")
        app.HISTORY_FILE = os.path.join(data, "mod_history.json")
        app.SETTINGS_FILE = os.path.join(data, "settings.json")
        app.ensure_data_dirs()

    def tearDown(self):
        for k, v in self._old.items():
            setattr(app, k, v)

    def test_mod_history_empty_by_default(self):
        self.assertEqual(app.mod_history(), {"applied": []})

    def test_log_mod_appends_entry(self):
        app.log_mod("selftest", "hello", 3)
        hist = app.mod_history()
        self.assertEqual(len(hist["applied"]), 1)
        self.assertEqual(hist["applied"][0]["kind"], "selftest")
        self.assertEqual(hist["applied"][0]["detail"], "hello")
        self.assertEqual(hist["applied"][0]["n"], 3)

    def test_log_mod_caps_history_at_1000(self):
        for i in range(1050):
            app.log_mod("bulk", i)
        hist = app.mod_history()
        self.assertEqual(len(hist["applied"]), 1000)
        self.assertEqual(hist["applied"][-1]["detail"], 1049)

    def test_mod_history_ignores_corrupt_json(self):
        with open(app.HISTORY_FILE, "w", encoding="utf-8") as f:
            f.write("{ not json")
        self.assertEqual(app.mod_history(), {"applied": []})

    def test_ensure_data_dirs_creates_tree(self):
        ok = app.ensure_data_dirs()
        self.assertTrue(ok)
        for d in (app.DATA_DIR, app.CACHE_ROOT, app.TMP_DIR, app.BACKUP_DIR, app.LOG_DIR):
            self.assertTrue(os.path.isdir(d), d)

    def test_ensure_data_dirs_migrates_legacy_settings(self):
        legacy = os.path.join(app.PROJECT_DIR, "nh_mod_tool_settings.json")
        created = False
        if not os.path.exists(legacy):
            with open(legacy, "w", encoding="utf-8") as f:
                json.dump({"assets": "X"}, f)
            created = True
        try:
            app.ensure_data_dirs()
            self.assertTrue(os.path.isfile(app.SETTINGS_FILE))
        finally:
            if created:
                os.remove(legacy)

    def test_cache_dir_is_deterministic_and_path_specific(self):
        a = app.cache_dir("C:/game/a/sharedassets0.assets")
        b = app.cache_dir("C:/game/a/sharedassets0.assets")
        c = app.cache_dir("C:/game/b/sharedassets0.assets")
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertTrue(os.path.basename(a).startswith("nh_thumbcache_"))


if __name__ == "__main__":
    unittest.main()