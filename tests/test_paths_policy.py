# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import NHModTool as app  # noqa: E402


class PathHelpersTest(unittest.TestCase):
    def test_norm_dirname_strips_punctuation_and_case(self):
        self.assertEqual(app._norm_dirname("No, I'm not a Human"), "noimnotahuman")
        self.assertEqual(app._norm_dirname("No I'm not a Human"), "noimnotahuman")
        self.assertEqual(app._norm_dirname("NoImNotAHuman_Data"), "noimnotahumandata")

    def test_target_norms_cover_both_game_variants(self):
        for variant in app.GAME_DIR_VARIANTS:
            self.assertIn(app._norm_dirname(variant), app._TARGET_NORMS)

    def test_game_dir_variants_include_comma_form(self):
        self.assertIn("No, I'm not a Human", app.GAME_DIR_VARIANTS)
        self.assertIn("No I'm not a Human", app.GAME_DIR_VARIANTS)

    def test_assets_name_is_expected(self):
        self.assertEqual(app.ASSETS_NAME, "sharedassets0.assets")

    def test_steam_libraries_parses_paths(self):
        import tempfile
        vdf = os.path.join(tempfile.mkdtemp(), "libraryfolders.vdf")
        with open(vdf, "w", encoding="utf-8") as f:
            f.write('"libraryfolders"\n{\n"0"\n{\n"path"\t"D:\\SteamLibrary"\n}\n}')
        libs = app.steam_libraries(vdf)
        self.assertIn("D:\\SteamLibrary", libs)

    def test_steam_libraries_missing_file_is_safe(self):
        self.assertEqual(app.steam_libraries("Z:\\nope\\missing.vdf"), [])


if __name__ == "__main__":
    unittest.main()