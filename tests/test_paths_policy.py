# -*- coding: utf-8 -*-
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import NHModTool as app  # noqa: E402
from theme import PALETTE, TYPOGRAPHY  # noqa: E402


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


class ThemeTest(unittest.TestCase):
    REQUIRED_TOKENS = (
        "bg.base",
        "bg.surface",
        "bg.elevated",
        "bg.overlay",
        "text.primary",
        "text.secondary",
        "text.muted",
        "text.inverse",
        "border.subtle",
        "border.default",
        "border.focus",
        "accent.primary",
        "accent.hover",
        "accent.pressed",
        "accent.solid",
        "state.danger",
        "state.success_text",
    )

    def test_theme_palette_has_required_tokens(self):
        self.assertGreaterEqual(len(PALETTE), 15)
        for token in self.REQUIRED_TOKENS:
            self.assertIn(token, PALETTE, "missing palette token %r" % token)

    def test_theme_palette_values_are_hex(self):
        hex_re = re.compile(r"^#[0-9A-Fa-f]{6}$")
        for key, value in PALETTE.items():
            self.assertRegex(value, hex_re, "PALETTE[%r]=%r is not a hex color" % (key, value))

    def test_no_hardcoded_hex_outside_theme(self):
        src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "NHModTool.py")
        with open(src_path, "r", encoding="utf-8") as fh:
            source = fh.read()
        matches = re.findall(r"#[0-9A-Fa-f]{6}\b", source)
        self.assertEqual(matches, [],
                         "NHModTool.py still contains hardcoded hex colors: %r" % matches)

    def _button_style_assignments(self):
        src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "NHModTool.py")
        with open(src_path, "r", encoding="utf-8-sig") as fh:
            source = fh.read()
        assignments = []
        # Match both ttk.Button and ttkb.Button
        for match in re.finditer(r"(?:ttk|ttkb)\.Button\(", source):
            start = match.start()
            depth = 1
            i = match.end()
            while i < len(source) and depth:
                if source[i] == "(":
                    depth += 1
                elif source[i] == ")":
                    depth -= 1
                i += 1
            call = source[start:i]
            line_no = source.count("\n", 0, start) + 1
            # Match style= but not bootstyle=
            style = re.search(r'(?<!boot)style\s*=\s*"([^"]+)"', call)
            assignments.append((line_no, call, style.group(1) if style else None))
        return assignments

    def test_all_buttons_have_explicit_style(self):
        """Check that all ttk/ttkb.Button calls have either style= (string literal or variable) or bootstyle=."""
        src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "NHModTool.py")
        with open(src_path, "r", encoding="utf-8-sig") as fh:
            source = fh.read()
        missing = []
        for match in re.finditer(r"(?:ttk|ttkb)\.Button\(", source):
            start = match.start()
            depth = 1
            i = match.end()
            while i < len(source) and depth:
                if source[i] == "(":
                    depth += 1
                elif source[i] == ")":
                    depth -= 1
                i += 1
            call = source[start:i]
            line_no = source.count("\n", 0, start) + 1
            # Check for style= (string literal or variable) or bootstyle=
            has_style = re.search(r'(?<!boot)style\s*=', call)
            has_bootstyle = re.search(r'bootstyle\s*=', call)
            if not has_style and not has_bootstyle:
                missing.append(line_no)
        self.assertEqual(missing, [], "ttk/ttkb.Button without style= or bootstyle= at line(s): %r" % missing)

    def test_button_styles_are_known(self):
        known = {
            "Primary.TButton", "Secondary.TButton", "Danger.TButton", "Ghost.TButton",
            "ActionPrimary.TButton", "ActionSecondary.TButton", "danger.TButton",
            "SidebarPassive.TButton", "SidebarActive.TButton",
            "secondary-outline",  # used via bootstyle=
        }
        unknown = [(line, style) for line, call, style in self._button_style_assignments()
                   if style and style not in known]
        self.assertEqual(unknown, [], "unknown button style(s): %r" % unknown)

    def test_no_tk_button_in_module(self):
        src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "NHModTool.py")
        with open(src_path, "r", encoding="utf-8-sig") as fh:
            source = fh.read()
        hits = re.findall(r"\btk\.Button\(", source)
        self.assertEqual(hits, [], "plain tk.Button (non-ttk) is not allowed: %r" % hits)


if __name__ == "__main__":
    unittest.main()