# -*- coding: utf-8 -*-
import json
import logging.handlers
import os
import sys
import tempfile
import threading
import types
import unittest
from unittest import mock

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

    def test_settings_valid_passes_through(self):
        raw = dict(app.DEFAULT_SETTINGS)
        validated, warnings = app.validate_settings(raw)
        self.assertEqual(validated, raw)
        self.assertEqual(warnings, [])

    def test_settings_missing_keys_filled_with_defaults(self):
        validated, warnings = app.validate_settings({})
        self.assertEqual(validated, app.DEFAULT_SETTINGS)
        self.assertEqual(warnings, [])

    def test_settings_wrong_type_replaced_with_default(self):
        raw = dict(app.DEFAULT_SETTINGS)
        raw["backup_interval_minutes"] = "abc"
        validated, warnings = app.validate_settings(raw)
        self.assertEqual(validated["backup_interval_minutes"],
                         app.DEFAULT_SETTINGS["backup_interval_minutes"])
        self.assertGreaterEqual(len(warnings), 1)

    def test_settings_invalid_language_falls_back(self):
        raw = dict(app.DEFAULT_SETTINGS)
        raw["language"] = "de"
        validated, warnings = app.validate_settings(raw)
        self.assertEqual(validated["language"], "en")
        self.assertGreaterEqual(len(warnings), 1)

    def test_settings_invalid_theme_falls_back(self):
        raw = dict(app.DEFAULT_SETTINGS)
        raw["theme"] = "purple"
        validated, warnings = app.validate_settings(raw)
        self.assertEqual(validated["theme"], "dark")
        self.assertGreaterEqual(len(warnings), 1)

    def test_settings_negative_interval_clamped(self):
        raw = dict(app.DEFAULT_SETTINGS)
        raw["backup_interval_minutes"] = -5
        validated, warnings = app.validate_settings(raw)
        self.assertGreaterEqual(validated["backup_interval_minutes"], 1)
        self.assertGreaterEqual(len(warnings), 1)

    def test_settings_unknown_keys_preserved(self):
        validated, warnings = app.validate_settings({"custom_future_key": 42})
        self.assertIn("custom_future_key", validated)
        self.assertEqual(validated["custom_future_key"], 42)

    def test_settings_not_a_dict_returns_defaults(self):
        for raw in ([], None, "string"):
            validated, warnings = app.validate_settings(raw)
            self.assertEqual(validated, {})
            self.assertGreaterEqual(len(warnings), 1)

    def test_load_settings_corrupt_json_creates_backup(self):
        with open(app.SETTINGS_FILE, "w", encoding="utf-8") as f:
            f.write("{ not json")
        app.load_language(app.KNOWN_LANGUAGES[0])
        instance = object.__new__(app.App)
        orig_warn = app.messagebox.showwarning
        app.messagebox.showwarning = lambda *a, **k: None
        try:
            prefs = instance.load_prefs()
        finally:
            app.messagebox.showwarning = orig_warn
        self.assertEqual(prefs, app.DEFAULT_SETTINGS)
        baks = [n for n in os.listdir(os.path.dirname(app.SETTINGS_FILE))
                if n.startswith("settings.json.bak.")]
        self.assertEqual(len(baks), 1)

    # ---------------- window geometry settings ----------------

    def test_default_settings_has_window_geometry(self):
        self.assertIn("window.geometry", app.DEFAULT_SETTINGS)
        self.assertEqual(app.DEFAULT_SETTINGS["window.geometry"], "")

    def test_validate_settings_window_geometry_valid(self):
        raw = dict(app.DEFAULT_SETTINGS)
        raw["window.geometry"] = "1100x720+100+50"
        validated, warnings = app.validate_settings(raw)
        self.assertEqual(validated["window.geometry"], "1100x720+100+50")
        self.assertEqual(warnings, [])

    def test_validate_settings_window_geometry_invalid_falls_back(self):
        for bad in ("abc", "1100", "1100x720x300", 12345):
            raw = dict(app.DEFAULT_SETTINGS)
            raw["window.geometry"] = bad
            validated, warnings = app.validate_settings(raw)
            self.assertEqual(validated["window.geometry"], "",
                             "bad value %r must fall back to empty string" % bad)
            self.assertGreaterEqual(len(warnings), 1,
                                    "bad value %r must produce a warning" % bad)

    def test_window_geometry_regex_pattern(self):
        pattern = app.WINDOW_GEOMETRY_RE
        for good in ("800x600", "800x600+10+20", "800x600-10-20",
                     "1100x720", "1100x720+100+50"):
            self.assertIsNotNone(pattern.match(good), "must match: %r" % good)
        for bad in ("abc", "800", "800x", "+10+20", "1100x720x300"):
            self.assertIsNone(pattern.match(bad), "must reject: %r" % bad)

    def test_geometry_offscreen_detection(self):
        self.assertTrue(callable(getattr(app, "_geometry_offscreen", None)))
        on = "800x600+10+20"
        self.assertFalse(app._geometry_offscreen(on, 1920, 1080))
        self.assertTrue(app._geometry_offscreen("800x600-10+20", 1920, 1080))
        self.assertTrue(app._geometry_offscreen("800x600+10-20", 1920, 1080))
        self.assertTrue(app._geometry_offscreen("800x600+1800+20", 1920, 1080))
        self.assertTrue(app._geometry_offscreen("1000x700+1500+800", 1920, 1080))
        self.assertFalse(app._geometry_offscreen("800x600", 1920, 1080))
        self.assertFalse(app._geometry_offscreen("800x600+10+20", 0, 0))


class LoggingAndPathsTest(unittest.TestCase):
    """Structural guarantees for logging and the writable data directory."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="nh_paths_")
        self._old = {
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
        os.makedirs(app.DATA_DIR, exist_ok=True)

    def tearDown(self):
        for k, v in self._old.items():
            setattr(app, k, v)

    def test_log_dir_under_data_dir(self):
        prefix = os.path.normcase(app.DATA_DIR) + os.sep
        self.assertTrue(os.path.normcase(app.LOG_DIR).startswith(prefix))

    def test_data_dir_is_writable(self):
        self.assertTrue(app.ensure_data_dirs())
        probe = os.path.join(app.DATA_DIR, "write_probe.tmp")
        with open(probe, "w", encoding="utf-8") as f:
            f.write("probe")
        self.assertTrue(os.path.isfile(probe))
        os.remove(probe)
        self.assertFalse(os.path.exists(probe))

    def test_logger_has_rotating_handler(self):
        rotating = [
            h for h in app.logger.handlers
            if isinstance(h, logging.handlers.RotatingFileHandler)
        ]
        self.assertEqual(len(rotating), 1)
        self.assertGreater(rotating[0].maxBytes, 0)
        self.assertGreater(rotating[0].backupCount, 0)

    def test_no_print_calls_in_module(self):
        source_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "NHModTool.py")
        with open(source_path, "r", encoding="utf-8") as f:
            source = f.read()
        self.assertNotIn("print(", source)


class LocaleParityTest(unittest.TestCase):
    """EN/TR locale parity tests; read the JSON files directly (no app)."""

    LOCALES_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "locales")

    def _load(self, name: str) -> dict:
        with open(os.path.join(self.LOCALES_DIR, name), "r", encoding="utf-8") as f:
            return json.load(f)

    def test_locale_files_have_identical_keys(self):
        en = self._load("en.json")
        tr = self._load("tr.json")
        self.assertEqual(set(en), set(tr))

    def test_locale_format_placeholders_match(self):
        en = self._load("en.json")
        tr = self._load("tr.json")
        mismatched = []
        for key in sorted(set(en) & set(tr)):
            e, t_val = en[key], tr[key]
            if not isinstance(e, str) or not isinstance(t_val, str):
                continue
            e_ph = (e.count("%s"), e.count("%d"), e.count("{"))
            t_ph = (t_val.count("%s"), t_val.count("%d"), t_val.count("{"))
            if e_ph != t_ph:
                mismatched.append((key, e_ph, t_ph))
        self.assertEqual(mismatched, [])

    def test_security_and_settings_keys_exist(self):
        required = {
            "security.delete_blocked",
            "security.cache_refresh_blocked",
            "security.dialog_title",
            "settings.corrupt_reset",
            "settings.corrected",
            "settings.dialog_title",
        }
        self.assertEqual(required - set(self._load("en.json")), set())
        self.assertEqual(required - set(self._load("tr.json")), set())


class GlobalExceptionHandlerTest(unittest.TestCase):
    """Global exception handlers: hooks installed, logging, dialog rules."""

    def setUp(self):
        self._sys_excepthook = sys.excepthook
        self._thread_excepthook = getattr(threading, "excepthook", None)
        self._active_app = app._ACTIVE_APP

    def tearDown(self):
        sys.excepthook = self._sys_excepthook
        if hasattr(threading, "excepthook"):
            threading.excepthook = self._thread_excepthook
        app._ACTIVE_APP = self._active_app

    def test_install_global_exception_handlers_sets_excepthook(self):
        app.install_global_exception_handlers()
        self.assertIs(sys.excepthook, app._handle_uncaught)
        self.assertIsNot(sys.excepthook, sys.__excepthook__)
        self.assertIs(threading.excepthook, app._handle_thread_uncaught)

    def test_install_binds_tk_callback_when_app_given(self):
        fake_app = types.SimpleNamespace(root=types.SimpleNamespace())
        app.install_global_exception_handlers(fake_app)
        self.assertIs(fake_app.root.report_callback_exception,
                      app._handle_tk_callback)
        self.assertIs(app._ACTIVE_APP, fake_app)

    def test_handle_uncaught_logs_exception(self):
        with mock.patch.object(app.logger, "exception") as exc_mock, \
             mock.patch.object(app.messagebox, "showerror") as mb_mock:
            try:
                raise ValueError("boom")
            except ValueError:
                exc_type, exc_value, exc_tb = sys.exc_info()
            app._handle_uncaught(exc_type, exc_value, exc_tb)
        exc_mock.assert_called_once()
        mb_mock.assert_called_once()
        self.assertEqual(exc_mock.call_args.kwargs["exc_info"][0], ValueError)

    def test_handle_uncaught_no_messagebox_when_no_exception(self):
        with mock.patch.object(app.logger, "exception") as exc_mock, \
             mock.patch.object(app.messagebox, "showerror") as mb_mock:
            app._handle_uncaught(ValueError, None, None)
        exc_mock.assert_called_once()
        mb_mock.assert_not_called()

    def test_handle_thread_uncaught_logs(self):
        thread = types.SimpleNamespace(name="worker-1")
        args = types.SimpleNamespace(
            exc_type=ValueError,
            exc_value=ValueError("boom"),
            exc_traceback=None,
            thread=thread)
        with mock.patch.object(app.logger, "exception") as exc_mock, \
             mock.patch.object(app, "_ACTIVE_APP", None):
            app._handle_thread_uncaught(args)
        exc_mock.assert_called_once()

    def test_handler_internal_error_does_not_raise(self):
        def exploding_dialog(*args, **kwargs):
            raise RuntimeError("dialog exploded")

        def silent_default(*args, **kwargs):
            return None

        original_default = sys.__excepthook__
        sys.__excepthook__ = silent_default
        try:
            with mock.patch.object(app.messagebox, "showerror",
                                   side_effect=exploding_dialog), \
                 mock.patch.object(app.logger, "exception") as exc_mock:
                app._handle_uncaught(ValueError, ValueError("boom"), None)
            exc_mock.assert_called_once()
        finally:
            sys.__excepthook__ = original_default


if __name__ == "__main__":
    unittest.main()