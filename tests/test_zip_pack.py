# -*- coding: utf-8 -*-
"""Photo Pack (ZIP) tests: import/matching, validation, security and a full
apply -> verify -> restore MD5 round trip against a COPY of the real asset
file (never the real file itself)."""
import io
import gc
import os
import shutil
import sys
import tempfile
import unittest
import zipfile
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import NHModTool as app  # noqa: E402


def _png_bytes(w=16, h=16, color=(180, 40, 40, 255)):
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGBA", (w, h), color).save(buf, format="PNG")
    return buf.getvalue()


def _jpg_bytes(w=16, h=16):
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (w, h), (10, 60, 200)).save(buf, format="JPEG")
    return buf.getvalue()


def _webp_bytes(w=16, h=16):
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGBA", (w, h), (200, 200, 10, 255)).save(buf, format="WEBP")
    return buf.getvalue()


def _gif_bytes(w=16, h=16):
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (w, h), (10, 200, 60)).save(buf, format="GIF")
    return buf.getvalue()


def _make_zip(path, files):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for arc, data in files.items():
            z.writestr(arc, data)


BY_NAME = {"fake_neighbour0": "fake_neighbour0", "fake_neighbour1": "fake_neighbour1",
           "fake_neighbour2": "fake_neighbour2", "fake_neighbour3": "fake_neighbour3"}


class ZipScanTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="nh_zip_")

    def _scan(self, files):
        zpath = os.path.join(self.tmp, "pack.zip")
        _make_zip(zpath, files)
        with zipfile.ZipFile(zpath) as z:
            return app._scan_zip_for_characters(z, BY_NAME), zpath

    def test_single_valid_image_matched(self):
        r, _ = self._scan({"fake_neighbour1.png": _png_bytes()})
        self.assertEqual(r["matches"], [("fake_neighbour1", "fake_neighbour1.png")])
        self.assertEqual(r["skipped"], [])
        self.assertEqual(r["unsafe"], [])

    def test_multiple_valid_images_matched(self):
        r, _ = self._scan({"fake_neighbour0.png": _png_bytes(color=(1, 2, 3, 255)),
                           "fake_neighbour1.png": _png_bytes(color=(4, 5, 6, 255)),
                           "fake_neighbour2.png": _png_bytes(color=(7, 8, 9, 255))})
        self.assertEqual(len(r["matches"]), 3)

    def test_mixed_formats_matched(self):
        r, _ = self._scan({"fake_neighbour0.png": _png_bytes(),
                           "fake_neighbour1.jpg": _jpg_bytes(),
                           "fake_neighbour2.webp": _webp_bytes(),
                           "fake_neighbour3.gif": _gif_bytes()})
        self.assertEqual(len(r["matches"]), 4)

    def test_folder_structure_uses_leaf_name(self):
        r, _ = self._scan({"chars/fake_neighbour2.png": _png_bytes()})
        self.assertEqual(r["matches"], [("fake_neighbour2", "chars/fake_neighbour2.png")])

    def test_filenames_with_spaces_do_not_crash(self):
        r, _ = self._scan({"my photo.png": _png_bytes(), "fake neighbour 1 .png": _png_bytes()})
        self.assertEqual(r["matches"], [])
        self.assertEqual(len(r["skipped"]), 2)

    def test_turkish_filename_does_not_crash(self):
        r, _ = self._scan({"foto\u011fraf.png": _png_bytes(), "fake_neighbour1.png": _png_bytes()})
        self.assertEqual(r["matches"], [("fake_neighbour1", "fake_neighbour1.png")])
        self.assertEqual(len(r["skipped"]), 1)

    def test_non_image_files_ignored(self):
        r, _ = self._scan({"readme.txt": b"x", "notes.json": b"{}",
                           "__MACOSX/.DS_Store": b"", "fake_neighbour1.png": _png_bytes()})
        self.assertEqual(r["matches"], [("fake_neighbour1", "fake_neighbour1.png")])
        self.assertEqual(r["skipped"], [])
        self.assertEqual(r["unsafe"], [])

    def test_missing_characters_all_skipped(self):
        r, _ = self._scan({"unknown1.png": _png_bytes(), "nobody.png": _png_bytes()})
        self.assertEqual(r["matches"], [])
        self.assertEqual(len(r["skipped"]), 2)

    def test_duplicate_stem_last_wins(self):
        r, _ = self._scan({"v1/fake_neighbour1.png": _png_bytes(color=(1, 0, 0, 255)),
                           "v2/fake_neighbour1.png": _png_bytes(color=(0, 1, 0, 255))})
        self.assertEqual(r["matches"], [("fake_neighbour1", "v2/fake_neighbour1.png")])
        self.assertEqual(len(r["dupes"]), 1)

    def test_large_image_skipped(self):
        r, _ = self._scan({"fake_neighbour1.png": b"\x00" * 4096})
        with mock.patch.object(app, "MAX_ZIP_IMAGE_BYTES", 64):
            with zipfile.ZipFile(os.path.join(self.tmp, "pack.zip")) as z:
                r2 = app._scan_zip_for_characters(z, BY_NAME)
        self.assertEqual(r2["matches"], [])
        self.assertEqual(len(r2["too_large"]), 1)

    def test_path_traversal_blocked(self):
        r, _ = self._scan({"../evil.png": _png_bytes(),
                           "..\\evil2.png": _png_bytes(),
                           "C:\\evil3.png": _png_bytes(),
                           "/abs/evil4.png": _png_bytes(),
                           "a/../../evil5.png": _png_bytes(),
                           "fake_neighbour1.png": _png_bytes()})
        self.assertEqual(len(r["unsafe"]), 5)
        self.assertEqual(r["matches"], [("fake_neighbour1", "fake_neighbour1.png")])


class ZipReadTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="nh_zipread_")

    def test_open_garbage_raises_user_friendly(self):
        zpath = os.path.join(self.tmp, "broken.zip")
        with open(zpath, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n not a zip at all")
        with self.assertRaises(app.PhotoPackError) as ctx:
            app._open_zip(zpath)
        self.assertIn("ZIP", str(ctx.exception))

    def test_open_truncated_zip_reported(self):
        zpath = os.path.join(self.tmp, "ok.zip")
        _make_zip(zpath, {"fake_neighbour1.png": _png_bytes()})
        data = open(zpath, "rb").read()
        trunc = os.path.join(self.tmp, "trunc.zip")
        with open(trunc, "wb") as f:
            f.write(data[: len(data) // 2])
        with self.assertRaises(app.PhotoPackError):
            app._open_zip(trunc)

    def test_corrupt_image_member_error(self):
        zpath = os.path.join(self.tmp, "badimg.zip")
        _make_zip(zpath, {"fake_neighbour1.png": b"not an image at all"})
        with zipfile.ZipFile(zpath) as z:
            prepared, errors = app._collect_zip_images(z, [("fake_neighbour1", "fake_neighbour1.png")])
        self.assertEqual(prepared, {})
        self.assertEqual(len(errors), 1)
        self.assertIn("fake_neighbour1.png", str(errors[0]))

    def test_encrypted_member_error(self):
        zpath = os.path.join(self.tmp, "enc.zip")
        _make_zip(zpath, {"fake_neighbour0.png": _png_bytes()})
        with zipfile.ZipFile(zpath) as z:
            with mock.patch.object(z, "read", side_effect=RuntimeError("File is encrypted")):
                prepared, errors = app._collect_zip_images(z, [("fake_neighbour0", "fake_neighbour0.png")])
        self.assertEqual(prepared, {})
        self.assertTrue(any("password" in str(e) for e in errors))

    def test_unsupported_compression_error(self):
        zpath = os.path.join(self.tmp, "comp.zip")
        _make_zip(zpath, {"fake_neighbour0.png": _png_bytes()})
        with zipfile.ZipFile(zpath) as z:
            with mock.patch.object(z, "read", side_effect=NotImplementedError("compress")):
                prepared, errors = app._collect_zip_images(z, [("fake_neighbour0", "fake_neighbour0.png")])
        self.assertEqual(prepared, {})
        self.assertTrue(any("compression" in str(e) for e in errors))

    def test_valid_member_collected_as_rgba(self):
        zpath = os.path.join(self.tmp, "ok.zip")
        _make_zip(zpath, {"fake_neighbour1.png": _png_bytes()})
        with zipfile.ZipFile(zpath) as z:
            prepared, errors = app._collect_zip_images(z, [("fake_neighbour1", "fake_neighbour1.png")])
        self.assertEqual(errors, [])
        self.assertEqual(list(prepared.keys()), ["fake_neighbour1"])
        self.assertEqual(prepared["fake_neighbour1"].mode, "RGBA")


class ZipSafetyTest(unittest.TestCase):
    def test_unsafe_name_patterns_all_rejected(self):
        cases = ["../x.png", "..\\x.png", "../../deep/x.png", "C:\\x.png",
                 "c:/x.png", "/x.png", "\\x.png", "a/../../x.png"]
        for c in cases:
            self.assertTrue(app._is_unsafe_zip_name(c.replace("\\", "/")),
                            "%r should be unsafe" % c)
        safe = ["fake_neighbour1.png", "chars/fake_neighbour2.png", "a b.png"]
        for c in safe:
            self.assertFalse(app._is_unsafe_zip_name(c))


class ZipEndToEndTest(unittest.TestCase):
    """Real apply (UnityPy) -> verify -> restore on a COPY. The real game file
    is only ever read for copying; it is never modified."""

    REAL = r"C:\Users\mehmet\AppData\Games\No, I'm not a Human" \
           r"\NoImNotAHuman_Data\sharedassets0.assets"

    def setUp(self):
        if not os.path.exists(self.REAL):
            self.skipTest("game not installed on this machine")
        self.base = tempfile.mkdtemp(prefix="nh_e2e_")
        self.resS = self.REAL + ".resS"

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def _game_copy(self):
        """Copy the real asset (and its .resS sibling) into this test's temp
        game folder. The real file is only read; the copy is what gets modded."""
        game_dir = os.path.join(self.base, "NoImNotAHuman_Data")
        os.makedirs(game_dir, exist_ok=True)
        copy = os.path.join(game_dir, app.ASSETS_NAME)
        shutil.copy2(self.REAL, copy)
        if os.path.exists(self.resS):
            shutil.copy2(self.resS, os.path.join(game_dir, app.ASSETS_NAME + ".resS"))
        return copy

    def _find_fake_character(self, env):
        for obj in env.objects:
            if obj.type.name != "Texture2D":
                continue
            try:
                d = obj.read()
            except Exception:
                continue
            n = d.m_Name or ""
            if n.lower().startswith("fake_"):
                return n
        return None

    def test_full_zip_apply_verify_restore_cycle(self):
        import UnityPy
        copy = self._game_copy()
        orig_md5 = app.file_md5(copy)
        self.assertEqual(orig_md5, app.file_md5(self.REAL), "copy must equal original")

        env = UnityPy.load(copy)
        name = self._find_fake_character(env)
        del env
        gc.collect()
        self.assertTrue(name, "no fake_ texture found in the copy")

        zip_path = os.path.join(self.base, "pack.zip")
        _make_zip(zip_path, {"%s.png" % name: _png_bytes(w=24, h=24)})
        out_dir = os.path.join(self.base, "dump")

        n = app.apply_zip_to_file(copy, zip_path, [(name, "%s.png" % name)],
                                  status=None, out_dir=out_dir)
        self.assertEqual(n, 1)
        self.assertNotEqual(orig_md5, app.file_md5(copy), "apply must change the copy")

        # verify the copy differs from the untouched original
        ok, changed = app._verify_objects(self.REAL, copy, set())
        self.assertFalse(ok)  # copy differs from original

        # restore from the automatic .bak and prove byte-identical round trip
        bak = os.path.join(os.path.dirname(copy), app.ASSETS_NAME + ".bak")
        self.assertTrue(os.path.isfile(bak), "automatic .bak backup must exist")
        app._atomic_replace(bak, copy)
        self.assertEqual(orig_md5, app.file_md5(copy), "restored copy must == original MD5")
        self.assertEqual(os.path.getsize(copy), os.path.getsize(self.REAL))

    def test_apply_existing_backup_is_not_overwritten(self):
        import UnityPy
        copy = self._game_copy()
        bak = os.path.join(os.path.dirname(copy), app.ASSETS_NAME + ".bak")
        with open(bak, "wb") as f:
            f.write(b"KEEP-ME")
        env = UnityPy.load(copy)
        name = self._find_fake_character(env)
        del env
        gc.collect()
        zip_path = os.path.join(self.base, "pack2.zip")
        _make_zip(zip_path, {"%s.png" % name: _png_bytes(w=24, h=24)})
        app.apply_zip_to_file(copy, zip_path, [(name, "%s.png" % name)],
                              status=None, out_dir=os.path.join(self.base, "dump2"))
        with open(bak, "rb") as f:
            self.assertEqual(f.read(), b"KEEP-ME")


if __name__ == "__main__":
    unittest.main()