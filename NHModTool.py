# ---------------------------------------------------------------
#  No, I'm not a Human - Mod Tool
#  A desktop utility for recoloring character textures, injecting
#  custom photos, applying bulk image packs, and managing the
#  game's backups. All project data lives under ./data/.
#
#  Author: S1VRA  (https://github.com/S1VRA)
# ---------------------------------------------------------------
import os, sys, io, shutil, json, queue, threading, hashlib, zipfile, re, logging, gc, stat, math, time
import logging.handlers
from pathlib import Path
from typing import Callable
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, filedialog, messagebox
import ttkbootstrap as ttkb

import UnityPy
from i18n import t, load_language, get_current_language
from PIL import Image, ImageDraw, ImageTk
from theme import PALETTE, TYPOGRAPHY, SPACING

APP_VERSION = "0.5.0"
APP_TITLE = "No, I'm not a Human - Mod Tool"
APP_NAME = "NH Mod Tool"
APP_DATA_DIR_NAME = "NHModTool"
ASSETS_NAME = "sharedassets0.assets"
GAME_DIR_NAME = "No I'm not a Human"
GAME_DIR_VARIANTS = (GAME_DIR_NAME, "No, I'm not a Human")
DATA_DIR_NAME = "NoImNotAHuman_Data"
_TARGET_NORMS = {"noimnotahuman", "noimnotahuman_data"}


def _norm_dirname(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())

_IS_FROZEN = bool(getattr(sys, "frozen", False))
if _IS_FROZEN:
    PROJECT_DIR = os.path.dirname(os.path.abspath(sys.executable))
    BUNDLE_DIR = getattr(sys, "_MEIPASS", PROJECT_DIR)
else:
    PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
    BUNDLE_DIR = PROJECT_DIR
if _IS_FROZEN:
    # Frozen EXEs must not write beside the executable (e.g. Program Files),
    # so user data lives under %APPDATA% (home directory is the fallback).
    DATA_DIR = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"),
                            APP_DATA_DIR_NAME)
else:
    DATA_DIR = os.path.join(PROJECT_DIR, "data")
CACHE_ROOT = os.path.join(DATA_DIR, "cache")
TMP_DIR = os.path.join(DATA_DIR, "tmp")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
HISTORY_FILE = os.path.join(DATA_DIR, "mod_history.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
LEGACY_SETTINGS_FILE = os.path.join(PROJECT_DIR, "nh_mod_tool_settings.json")
OUT_DIR = TMP_DIR
LOG_DIR = os.path.join(DATA_DIR, "logs")
APP_LOG_PATH = os.path.join(LOG_DIR, "app.log")
LOGGER_NAME = "nhmodtool"

# ------------------------------------------------- settings schema

# Known settings.json keys with their defaults. "theme" and
# "backup_interval_minutes" are documented forward-looking keys (they are not
# consumed by the app yet) but are still normalised so a malformed file never
# reaches the code unguarded. Unknown keys are preserved untouched.
DEFAULT_SETTINGS: dict[str, object] = {
    "assets": "",
    "photo_dir": "",
    "language": "en",
    "zoom": 1.0,
    "theme": "dark",
    "backup_interval_minutes": 60,
    "window.geometry": "",
}
KNOWN_LANGUAGES: tuple[str, ...] = ("en", "tr")
KNOWN_THEMES: tuple[str, ...] = ("dark", "light")
BACKUP_INTERVAL_MIN: int = 1
BACKUP_INTERVAL_MAX: int = 10080

# --------------------------------------------------- window policy

MIN_WINDOW_WIDTH: int = 1000
MIN_WINDOW_HEIGHT: int = 680
DEFAULT_WINDOW_GEOMETRY: str = "1100x720"
WINDOW_GEOMETRY_RE = re.compile(r"^\d+x\d+([+-]\d+[+-]\d+)?$")
EMPTY_STATE_WRAPLENGTH: int = 480

# ---------------------------------------------------------------- logging

def _setup_logging():
    """Rotating file logger under <DATA_DIR>/logs/app.log plus a WARNING
    console handler when stderr is available. Never crashes the app."""
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        handler = logging.handlers.RotatingFileHandler(
            APP_LOG_PATH, maxBytes=1024 * 1024, backupCount=2, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s  %(levelname)s  %(message)s"))
        root = logging.getLogger(LOGGER_NAME)
        root.setLevel(logging.DEBUG if os.environ.get("NHMODTOOL_DEBUG") else logging.INFO)
        root.addHandler(handler)
        if sys.stderr is not None:
            console = logging.StreamHandler(sys.stderr)
            console.setLevel(logging.WARNING)
            console.setFormatter(logging.Formatter("%(levelname)s  %(message)s"))
            root.addHandler(console)
        root.propagate = False
    except Exception:
        logging.getLogger(LOGGER_NAME).warning("logging setup failed", exc_info=True)


_setup_logging()
logger = logging.getLogger(LOGGER_NAME)


def log_exception(context):
    try:
        logger.exception(context)
    except Exception:
        pass


_ACTIVE_APP: "App | None" = None


def _error_title() -> str:
    """Translated dialog title; falls back to the generic error title and
    finally to a plain literal before i18n is seeded."""
    title = t("unhandled.title")
    if not title or title == "unhandled.title":
        title = t("common.error")
    if not title or title == "common.error":
        return "Error"
    return title


def _copy_error_text(top: "tk.Toplevel", message: str) -> None:
    """Put the summary text on the clipboard (tracebacks stay in the log)."""
    try:
        top.clipboard_clear()
        top.clipboard_append(message)
    except Exception:
        logger.debug("could not copy error details to the clipboard")


def _show_error_dialog(title: str, message: str) -> None:
    """Modal dialog showing only a short summary (never a raw traceback),
    with a button that copies the text; falls back to messagebox.showerror
    when no Tk root exists yet, so startup cannot crash inside the handler."""
    root = getattr(tk, "_default_root", None)
    try:
        live = root is not None and bool(root.winfo_exists())
    except Exception:
        live = False
    if not live:
        messagebox.showerror(title, message)
        return
    try:
        top = tk.Toplevel(root)
        top.title(title)
        top.transient(root)
        top.grab_set()
        top.resizable(False, False)
        tk.Label(top, text=message, justify=tk.LEFT, wraplength=520,
                 anchor=tk.W).pack(fill=tk.X, padx=16, pady=(14, 6))
        buttons = tk.Frame(top)
        buttons.pack(fill=tk.X, padx=16, pady=12)
        ttk.Button(buttons, text=t("unhandled.copy_details"), style="Ghost.TButton",
                   command=lambda: _copy_error_text(top, message)).pack(side=tk.RIGHT)
        ttk.Button(buttons, text=t("common.ok"), style="Primary.TButton", command=top.destroy).pack(
            side=tk.RIGHT, padx=(0, 8))
        top.protocol("WM_DELETE_WINDOW", top.destroy)
        top.wait_window(top)
    except Exception:
        messagebox.showerror(title, message)


def _report_uncaught(context: str, exc_type: type,
                     exc_value: BaseException | None, exc_tb: object) -> None:
    """Log the full traceback and surface a short, traceback-free dialog."""
    logger.exception(context, exc_info=(exc_type, exc_value, exc_tb))
    if exc_value is not None:
        _show_error_dialog(
            _error_title(),
            "%s\n\n%s\n\n%s" % (
                t("unhandled.summary") % exc_type.__name__,
                t("unhandled.log_path") % APP_LOG_PATH,
                t("unhandled.issues_hint")))


def _handle_uncaught(exc_type: type, exc_value: BaseException | None, exc_tb: object) -> None:
    """sys.excepthook: log and surface an uncaught main-thread exception."""
    try:
        _report_uncaught("Unhandled exception", exc_type, exc_value, exc_tb)
    except Exception:
        sys.__excepthook__(exc_type, exc_value, exc_tb)


def _handle_tk_callback(exc_type: type, exc_value: BaseException | None, exc_tb: object) -> None:
    """Tkinter report_callback_exception: log and surface callback errors."""
    try:
        _report_uncaught("Unhandled exception in Tk callback", exc_type, exc_value, exc_tb)
    except Exception:
        sys.__excepthook__(exc_type, exc_value, exc_tb)


def _handle_thread_uncaught(args: threading.ExceptHookArgs) -> None:
    """threading.excepthook: log the worker failure and post a status note to
    the UI queue when one exists; never pops a dialog from a background thread."""
    try:
        exc_type = getattr(args, "exc_type", None)
        exc_value = getattr(args, "exc_value", None)
        exc_tb = getattr(args, "exc_traceback", getattr(args, "exc_tb", None))
        thread_name = getattr(getattr(args, "thread", None), "name", "?")
        logger.exception("Unhandled exception in thread %s", thread_name,
                         exc_info=(exc_type, exc_value, exc_tb))
        active = _ACTIVE_APP
        if active is not None and hasattr(active, "q"):
            try:
                active.q.put(("status", t("unhandled.thread_status")))
            except Exception:
                logger.debug("could not post thread-failure status to the UI queue")
    except Exception:
        sys.__excepthook__(getattr(args, "exc_type", None),
                           getattr(args, "exc_value", None),
                           getattr(args, "exc_traceback", getattr(args, "exc_tb", None)))


def install_global_exception_handlers(app: "App | None" = None) -> None:
    """Install sys/threading excepthooks and, when an App is available, the
    Tk callback exception hook. Safe to call more than once."""
    global _ACTIVE_APP
    sys.excepthook = _handle_uncaught
    if hasattr(threading, "excepthook"):
        threading.excepthook = _handle_thread_uncaught
    if app is not None:
        _ACTIVE_APP = app
        app.root.report_callback_exception = _handle_tk_callback

# Backward-compatible alias dict for the legacy tk-widget call sites.
# Values are derived from the single token source (theme.PALETTE).
def _hex_to_rgb(hex_value):
    """Convert '#RRGGBB' to an (R, G, B) tuple for PIL drawing."""
    hex_value = hex_value.lstrip("#")
    return tuple(int(hex_value[i:i + 2], 16) for i in (0, 2, 4))


COLORS = {
    "bg": PALETTE["bg.base"],
    "half": PALETTE["bg.footer"],
    "card": PALETTE["bg.surface"],
    "panel": PALETTE["bg.elevated"],
    "border": PALETTE["border.subtle"],
    "text": PALETTE["text.primary"],
    "muted": PALETTE["text.muted"],
    "accent": PALETTE["accent.primary"],
    "accent2": PALETTE["accent.hover"],
    "ok": PALETTE["state.success"],
    "danger": PALETTE["state.danger"],
    "selected": PALETTE["accent.primary"],
    "selected_text": PALETTE["text.primary"],
    "cell_norm": _hex_to_rgb(PALETTE["gallery.cell_norm"]),
    "cell_sel": _hex_to_rgb(PALETTE["gallery.cell_sel"]),
    "menu_bg": PALETTE["bg.menu"],
}

FONT = TYPOGRAPHY["family"]
CARD_W = 138
CARD_H = 116
CELL_W = 122
CELL_H = 76
GAP = 12
THUMB_W = 240
THUMB_H = 160
# Checkerboard colors for transparency previews. The PIL board and the Tk
# board must show the same pattern, hence both an RGB and a hex form.
CHECKER_LIGHT_RGB = _hex_to_rgb(PALETTE["checker.light"])
CHECKER_DARK_RGB = _hex_to_rgb(PALETTE["checker.dark"])
CHECKER_LIGHT = PALETTE["checker.light"]
CHECKER_DARK = PALETTE["checker.dark"]
ZOOM_MIN = 0.5
ZOOM_MAX = 2.0
ZOOM_ADIM = 0.1


def make_cell(img, bg, g=CELL_W, y=CELL_H):
    cell = Image.new("RGBA", (g, y), bg + (255,))
    thumb = img.convert("RGBA")
    thumb.thumbnail((g - 8, y - 4), Image.BILINEAR)
    cell.paste(thumb, ((g - thumb.width) // 2, (y - thumb.height) // 2), thumb)
    return cell.convert("RGB")


def safe_name(name):
    return "".join(c if c.isalnum() else "_" for c in name)


def fmt_name(fmt):
    names = {98: "RGBA", 12: "DXT5", 29: "DXT5Crunched", 28: "DXT1", 62: "DXT1Crunched", 47: "BC7",
             3: "RGB24", 4: "RGBA32", 13: "RGBA4444", 1: "Alpha8"}
    return names.get(fmt, "fmt%d" % fmt)


def _add_listbox_hover(listbox, enter_bg, leave_bg):
    """Add simple hover highlighting to listbox items."""
    listbox.bind("<Enter>", lambda e: listbox.config(background=enter_bg))
    listbox.bind("<Leave>", lambda e: listbox.config(background=leave_bg))


def object_snapshots(path):
    env = UnityPy.load(path)
    snaps = {}
    for obj in env.objects:
        key = (obj.type.name, obj.path_id)
        try:
            snaps[key] = obj.get_raw_data()
        except Exception:
            snaps[key] = b"\x00UNREADABLE"
    return snaps


def _setting_warn(warnings: list[str], key: str, message: str) -> None:
    warnings.append("%s: %s" % (key, message))


def _validate_str_path(key: str, out: dict, warnings: list[str]) -> None:
    value = out.get(key, DEFAULT_SETTINGS[key])
    if not isinstance(value, str):
        out[key] = DEFAULT_SETTINGS[key]
        _setting_warn(warnings, key, "wrong type, reset to default")
        return
    if value and not os.path.exists(value):
        # The user may not have created the folder yet; keep the value.
        _setting_warn(warnings, key, "path does not exist yet, value kept")


def _validate_choice(key: str, out: dict, default: str, allowed: tuple[str, ...],
                     warnings: list[str]) -> None:
    value = out.get(key, default)
    if not isinstance(value, str):
        out[key] = default
        _setting_warn(warnings, key, "wrong type, reset to %s" % default)
        return
    value = value.lower()
    if value not in allowed:
        out[key] = default
        _setting_warn(warnings, key, "unsupported value, reset to %s" % default)
        return
    out[key] = value


def _validate_float(key: str, out: dict, default: float, warnings: list[str]) -> None:
    value = out.get(key, default)
    try:
        if isinstance(value, bool):
            raise ValueError("bool is not numeric")
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("not finite")
    except (TypeError, ValueError):
        out[key] = default
        _setting_warn(warnings, key, "not a valid number, reset to %s" % default)
        return
    out[key] = number


def _validate_int_range(key: str, out: dict, default: int, lo: int, hi: int,
                        warnings: list[str]) -> None:
    value = out.get(key, default)
    try:
        if isinstance(value, bool):
            raise ValueError("bool is not numeric")
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("not finite")
    except (TypeError, ValueError):
        out[key] = default
        _setting_warn(warnings, key, "not a valid number, reset to %s" % default)
        return
    number = int(number)
    if number < lo or number > hi:
        number = max(lo, min(hi, number))
        _setting_warn(warnings, key, "out of range, clamped to %s" % number)
    out[key] = number


def _validate_window_geometry(key: str, out: dict, default: str, warnings: list[str]) -> None:
    value = out.get(key, default)
    if not isinstance(value, str):
        out[key] = default
        _setting_warn(warnings, key, "wrong type, reset to default")
        return
    if value and not WINDOW_GEOMETRY_RE.match(value):
        out[key] = default
        _setting_warn(warnings, key, "invalid geometry format, reset to default")
        return
    out[key] = value


def _geometry_offscreen(geometry: str, screen_w: int, screen_h: int) -> bool:
    """Return True when a "WxH+X+Y" geometry lies outside the given screen
    (or has a negative origin). A bare "WxH" (no position, screen_w=0) or an
    unparseable string is never treated as offscreen."""
    if not geometry or screen_w <= 0 or screen_h <= 0:
        return False
    match = re.match(r"^(\d+)x(\d+)([+-]\d+)([+-]\d+)$", geometry)
    if not match:
        return False
    width, height = int(match.group(1)), int(match.group(2))
    x, y = int(match.group(3)), int(match.group(4))
    return x < 0 or y < 0 or x + width > screen_w or y + height > screen_h


def _geometry_size_only(geometry: str) -> str:
    """Strip the position from a "WxH+X+Y" geometry, returning "WxH"."""
    match = re.match(r"^\d+x\d+", geometry)
    return match.group(0) if match else ""


def _build_empty_state(parent: tk.Misc, title_key: str, body_key: str,
                       action_key: str, action_command: Callable,
                       icon: str = "") -> tk.Frame:
    """Reusable empty-state block: icon, large title, body, primary action.
    Returns the frame so the caller can pack/forget it between empty and populated content.
    Icon: 40pt, Title: 16pt bold, Padding: 32px total (16px each side)."""
    frame = tk.Frame(parent, bg=PALETTE["bg.base"])
    box = tk.Frame(frame, bg=PALETTE["bg.base"])
    box.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)  # 32px total padding

    if icon:
        ttk.Label(box, text=icon, font=("Segoe UI Emoji", 40),
                  foreground=PALETTE["text.muted"], background=PALETTE["bg.base"]).pack(pady=(0, 12))

    ttk.Label(box, text=t(title_key), font=("Segoe UI", 16, "bold"),
              foreground=PALETTE["text.primary"], background=PALETTE["bg.base"],
              anchor=tk.CENTER).pack(pady=(0, 8))
    ttk.Label(box, text=t(body_key), style="Muted.TLabel",
              anchor=tk.CENTER, justify=tk.CENTER,
              wraplength=EMPTY_STATE_WRAPLENGTH).pack(pady=(0, 16))
    ttk.Button(box, text=t(action_key), style="Primary.TButton",
               command=action_command).pack()
    return frame


def validate_settings(raw: object) -> tuple[dict, list[str]]:
    """Sanitise a raw settings payload against DEFAULT_SETTINGS.

    Missing known keys are filled with their defaults; wrong-typed or
    invalid values fall back to their defaults (one warning each); unknown
    keys are preserved untouched for forward compatibility. Returns the
    sanitised dict and a list of human-readable warnings.
    """
    if not isinstance(raw, dict):
        return {}, ["settings JSON is not an object; using defaults"]
    out = dict(raw)
    for key, value in DEFAULT_SETTINGS.items():
        out.setdefault(key, value)
    warnings: list[str] = []
    _validate_str_path("assets", out, warnings)
    _validate_str_path("photo_dir", out, warnings)
    _validate_choice("language", out, DEFAULT_SETTINGS["language"],
                     KNOWN_LANGUAGES, warnings)  # type: ignore[arg-type]
    _validate_choice("theme", out, DEFAULT_SETTINGS["theme"],
                     KNOWN_THEMES, warnings)  # type: ignore[arg-type]
    _validate_float("zoom", out, DEFAULT_SETTINGS["zoom"], warnings)  # type: ignore[arg-type]
    _validate_int_range("backup_interval_minutes", out,
                        DEFAULT_SETTINGS["backup_interval_minutes"],  # type: ignore[arg-type]
                        BACKUP_INTERVAL_MIN, BACKUP_INTERVAL_MAX, warnings)
    _validate_window_geometry("window.geometry", out,
                              str(DEFAULT_SETTINGS["window.geometry"]), warnings)
    return out, warnings


def _migrate_legacy_frozen_data() -> None:
    """One-time migration for frozen builds. Older versions kept user data
    next to the executable (PROJECT_DIR/data); current builds write under
    %APPDATA%. Copy settings, history and backups over when the new location
    does not have settings yet. Best-effort: failures are logged, never fatal."""
    if not _IS_FROZEN:
        return
    legacy_dir = os.path.join(PROJECT_DIR, "data")
    if not os.path.isdir(legacy_dir) or os.path.isfile(SETTINGS_FILE):
        return
    try:
        if os.path.normcase(os.path.realpath(legacy_dir)) == os.path.normcase(
                os.path.realpath(DATA_DIR)):
            return
        for name in ("settings.json", "mod_history.json"):
            src = os.path.join(legacy_dir, name)
            if os.path.isfile(src):
                shutil.copy2(src, os.path.join(DATA_DIR, name))
        legacy_backups = os.path.join(legacy_dir, "backups")
        if os.path.isdir(legacy_backups):
            for entry in os.listdir(legacy_backups):
                src = os.path.join(legacy_backups, entry)
                if os.path.isfile(src):
                    shutil.copy2(src, os.path.join(BACKUP_DIR, entry))
    except Exception as e:
        logger.warning("legacy data migration from %s failed: %s", legacy_dir, e)


def ensure_data_dirs():
    ok = True
    for d in (DATA_DIR, CACHE_ROOT, TMP_DIR, BACKUP_DIR, LOG_DIR):
        try:
            os.makedirs(d, exist_ok=True)
            if not os.access(d, os.W_OK):
                ok = False
        except Exception:
            ok = False
    _migrate_legacy_frozen_data()
    if not os.path.isfile(SETTINGS_FILE) and os.path.isfile(LEGACY_SETTINGS_FILE):
        try:
            shutil.copy2(LEGACY_SETTINGS_FILE, SETTINGS_FILE)
        except Exception:
            ok = False
    if not os.path.isfile(SETTINGS_FILE):
        try:
            with io.open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
        except Exception:
            ok = False
    return ok


def _atomic_replace(src, dst):
    """Copy to the destination directory and replace in one move so a partial
    write can never leave a half-written destination file behind."""
    folder = os.path.dirname(dst) or "."
    tmp = os.path.join(folder, os.path.basename(dst) + ".tmp")
    try:
        shutil.copy2(src, tmp)
        try:
            os.replace(tmp, dst)
        except PermissionError:
            # On Windows a still-open read handle (e.g. an unfinished UnityPy
            # environment) blocks os.replace; drop references and retry once.
            gc.collect()
            os.replace(tmp, dst)
    finally:
        try:
            if os.path.isfile(tmp):
                os.remove(tmp)
        except Exception:
            pass


def _ensure_free_space(folder, needed):
    try:
        free = shutil.disk_usage(folder).free
        if free < needed + (1 << 20):
            raise IOError("Not enough free disk space (need ~%d MB)."
                          % ((needed + (1 << 20)) // (1024 * 1024)))
    except IOError:
        raise
    except Exception:
        pass


# Anchored (non-user-configurable) roots that destructive operations may
# delete below. CACHE_ROOT is deliberately NOT listed: it must resolve under
# DATA_DIR anyway, so a redirected/junctioned cache can never widen the set
# of paths a deletion is allowed to touch.
MANAGED_ROOT_PATHS: list[Path] = [Path(DATA_DIR), Path(BACKUP_DIR)]


def is_under_managed_root(path: Path | str, roots: list[Path]) -> bool:
    """True when realpath(path) resolves inside one of realpath(roots).

    Both sides are symlink/junction-resolved first (os.path.realpath) and
    case-normalised, so a link that points outside a managed root can never
    pass the check and Windows drive-letter casing cannot bypass it either.
    """
    try:
        target = os.path.normcase(os.path.realpath(path))
    except Exception as e:
        logger.error("is_under_managed_root: cannot resolve target %s: %s", path, e)
        return False
    for root in roots:
        try:
            root_real = os.path.normcase(os.path.realpath(root))
        except Exception as e:
            logger.error("is_under_managed_root: cannot resolve root %s: %s", root, e)
            continue
        try:
            if os.path.commonpath([root_real, target]) == root_real:
                return True
        except ValueError:
            continue  # root and target sit on different drives
        except Exception as e:
            logger.error("is_under_managed_root: compare failed for %s: %s", path, e)
    return False


def cache_dir(assets):
    short = hashlib.md5(assets.encode("utf-8", "replace")).hexdigest()[:12]
    return os.path.join(CACHE_ROOT, "nh_thumbcache_%s" % short)


def mod_history():
    try:
        with io.open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict) and isinstance(data.get("applied"), list):
                return data
    except Exception:
        pass
    return {"applied": []}


# ---------------------------------------------------------------- photo pack core
# These helpers are tkinter-free so the exact same code path runs in the UI,
# in headless tests and inside the frozen exe (--assettest).

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}
MAX_ZIP_IMAGE_BYTES = 32 << 20
MAX_ZIP_TOTAL_BYTES = 2_000_000_000
MAX_ZIP_RATIO = 100
MAX_ZIP_MEMBERS = 5000


class PhotoPackError(Exception):
    """A ZIP/photo operation problem, phrased for the end user."""


_WINDOWS_DEVICE_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {"COM%d" % i for i in range(1, 10)}
    | {"LPT%d" % i for i in range(1, 10)})


def _windows_reserved_name(leaf: str) -> bool:
    """True when a file name collides with a Windows device name (CON, PRN,
    AUX, NUL, COM1-9, LPT1-9). These stay reserved even with an extension
    (CON.txt) or trailing dots/spaces."""
    stem = leaf.split(".", 1)[0].rstrip(" .").upper()
    return stem in _WINDOWS_DEVICE_NAMES


def _is_unsafe_zip_name(norm: str, root: str | None = None) -> bool:
    """String-level ZIP path safety check: absolute paths (/, C:\\, \\\\),
    ``..`` traversal and Windows reserved device names are rejected.

    When ``root`` is supplied the member path is additionally resolved with
    os.path.realpath and must stay inside the destination folder, so path
    traversal that survives the string checks cannot escape the root."""
    if norm.startswith("/") or norm.startswith("\\"):
        return True
    if re.match(r"^[A-Za-z]:", norm):
        return True
    if any(seg == ".." for seg in norm.split("/")):
        return True
    if _windows_reserved_name(norm.rsplit("/", 1)[-1]):
        return True
    if root is not None:
        try:
            root_real = os.path.realpath(root)
            segs = [s for s in norm.split("/") if s and s != "."]
            target = os.path.realpath(os.path.join(root_real, *segs))
        except Exception as e:
            logger.warning("Zip path check failed for %r: %s", norm, e)
            return True
        try:
            if os.path.commonpath([root_real, target]) != root_real:
                return True
        except ValueError:
            # realpath resolved to a different drive than the root.
            return True
    return False


def _zip_member_problem(inf, root: str | None = None) -> str | None:
    """Return a short reason when a ZIP member must be rejected, else None.

    Rejects empty names, symbolic-link members, and every path that
    _is_unsafe_zip_name flags (absolute, traversal, reserved device names,
    and - with ``root`` - paths resolving outside the destination)."""
    raw = (inf.filename or "").replace("\\", "/")
    if not raw:
        return "empty name"
    mode = (inf.external_attr >> 16) & 0xFFFF
    if mode and stat.S_ISLNK(mode):
        return "symbolic link"
    if _is_unsafe_zip_name(raw, root):
        return "unsafe path"
    return None


def _validate_zip_archive(z) -> None:
    """Zip-bomb scan that runs BEFORE any member is read or extracted.

    Raises PhotoPackError - naming the exceeded limit - when the archive has
    more than MAX_ZIP_MEMBERS files, unpacks to more than
    MAX_ZIP_TOTAL_BYTES, or compresses at more than MAX_ZIP_RATIO:1
    (per member or overall)."""
    total = 0
    total_compressed = 0
    count = 0
    for inf in z.infolist():
        if inf.is_dir():
            continue
        count += 1
        if count > MAX_ZIP_MEMBERS:
            raise PhotoPackError(
                "The ZIP exceeds the member-count limit (%d files; "
                "maximum allowed: %d)." % (count, MAX_ZIP_MEMBERS))
        total += inf.file_size
        total_compressed += inf.compress_size
        if total > MAX_ZIP_TOTAL_BYTES:
            raise PhotoPackError(
                "The ZIP exceeds the size limit: it would unpack to more than "
                "%d MB (maximum allowed: %d MB)."
                % (total // (1024 * 1024), MAX_ZIP_TOTAL_BYTES // (1024 * 1024)))
        if inf.compress_size > 0 and inf.file_size / inf.compress_size > MAX_ZIP_RATIO:
            raise PhotoPackError(
                "The ZIP exceeds the compression-ratio limit: \u201c%s\u201d "
                "expands at more than %d:1 (maximum allowed: %d:1). "
                "It may be a compressed bomb."
                % (inf.filename, MAX_ZIP_RATIO, MAX_ZIP_RATIO))
    if total_compressed > 0 and total / total_compressed > MAX_ZIP_RATIO:
        raise PhotoPackError(
            "The ZIP exceeds the compression-ratio limit overall "
            "(more than %d:1; maximum allowed: %d:1). It may be a compressed bomb."
            % (MAX_ZIP_RATIO, MAX_ZIP_RATIO))


def _open_zip(path):
    try:
        return zipfile.ZipFile(path)
    except zipfile.LargeZipFile:
        raise PhotoPackError("The ZIP file is too large to read.")
    except zipfile.BadZipFile:
        raise PhotoPackError(
            "Could not read the ZIP file \u201c%s\u201d.\nIt is not a ZIP archive or it is corrupt."
            % os.path.basename(path))
    except (OSError, IOError) as e:
        raise PhotoPackError("Could not open the ZIP file \u201c%s\u201d:\n%s"
                             % (os.path.basename(path), e))


def _iter_zip_images(z, root: str | None = None) -> list:
    out = []
    for i in z.infolist():
        if i.is_dir():
            continue
        raw = i.filename or ""
        if not raw:
            continue
        norm = raw.replace("\\", "/")
        leaf = norm.rsplit("/", 1)[-1]
        ext = os.path.splitext(leaf)[1].lower()
        problem = _zip_member_problem(i, root)
        out.append({"member": raw, "leaf": leaf, "ext": ext, "size": i.file_size,
                    "unsafe": problem is not None, "unsafe_reason": problem})
    return out


def _scan_zip_for_characters(z, by_name, root: str | None = None) -> dict:
    _validate_zip_archive(z)
    matches = {}
    skipped, unsafe, too_large, dupes = [], [], [], []
    for inf in _iter_zip_images(z, root):
        if inf["unsafe"]:
            unsafe.append(inf["member"])
            logger.warning("Blocked unsafe ZIP member %r (%s)",
                           inf["member"], inf["unsafe_reason"])
            continue
        if inf["ext"] not in IMAGE_EXTS:
            continue
        if inf["size"] > MAX_ZIP_IMAGE_BYTES:
            too_large.append(inf["member"])
            continue
        stem = os.path.splitext(inf["leaf"])[0].lower()
        if stem in by_name:
            if stem in matches:
                dupes.append(inf["member"])
            matches[stem] = (by_name[stem], inf["member"])
        else:
            skipped.append(inf["member"])
    return {"matches": list(matches.values()), "skipped": skipped,
            "unsafe": unsafe, "too_large": too_large, "dupes": dupes}


_IMAGE_MAGIC = {
    ".png": (b"\x89PNG\r\n\x1a\n",),
    ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",),
    ".gif": (b"GIF87a", b"GIF89a"),
    ".bmp": (b"BM",),
}


def _verify_image_magic(ext: str, data: bytes) -> bool:
    """Cheap header check: the member content must match its image extension.

    WebP uses the RIFF framing, so it is verified with its own pattern."""
    if ext == ".webp":
        return len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP"
    for sig in _IMAGE_MAGIC.get(ext, ()):
        if data.startswith(sig):
            return True
    return False


def _collect_zip_images(z, items, status=None):
    prepared = {}
    errors = []
    for name, member in items:
        try:
            data = z.read(member)
        except NotImplementedError:
            errors.append(PhotoPackError(
                "The image \u201c%s\u201d uses an unsupported compression type." % member))
            continue
        except RuntimeError:
            errors.append(PhotoPackError(
                "\u201c%s\u201d is inside a password-protected ZIP; password-protected archives are not supported."
                % member))
            continue
        except Exception:
            errors.append(PhotoPackError(
                "Could not read \u201c%s\u201d from the ZIP \u2014 the archive seems corrupt." % member))
            continue
        ext = os.path.splitext(member)[1].lower()
        if not _verify_image_magic(ext, data):
            errors.append(PhotoPackError(
                "The content of \u201c%s\u201d does not match its image type "
                "(PNG/JPEG/WebP/BMP/GIF); the file was rejected." % member))
            continue
        try:
            img = Image.open(io.BytesIO(data))
            img.load()
            img = img.convert("RGBA")
        except Exception:
            errors.append(PhotoPackError("\u201c%s\u201d is not a readable image." % member))
            continue
        prepared[name] = img
    return prepared, errors


def _find_texture(env, name):
    for obj in env.objects:
        if obj.type.name != "Texture2D":
            continue
        try:
            d = obj.read()
        except Exception:
            continue
        if (d.m_Name or "") == name:
            return obj, d
    return None, None


def _prep_sheet(img, w, h):
    sheet = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    k = img.copy()
    k.thumbnail((w, h), Image.LANCZOS)
    sheet.paste(k, ((w - k.width) // 2, (h - k.height) // 2), k)
    return sheet


def _write_env_dump(env, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    for fn in os.listdir(out_dir):
        p = os.path.join(out_dir, fn)
        try:
            if os.path.isfile(p):
                os.remove(p)
        except Exception:
            pass
    env.save(pack="none", out_path=out_dir)
    return os.path.join(out_dir, ASSETS_NAME)


def _verify_objects(original, modified, allowed):
    snap_orig = object_snapshots(original)
    snap_new = object_snapshots(modified)
    changed = []
    for k in snap_orig:
        if k not in snap_new or snap_orig[k] != snap_new[k]:
            changed.append(k)
    for k in snap_new:
        if k not in snap_orig:
            changed.append(k)
    return set(changed) == set(allowed), changed


def _commit_modified(original, modified):
    folder = os.path.dirname(original)
    _ensure_free_space(folder, os.path.getsize(modified))
    backup = os.path.join(folder, ASSETS_NAME + ".bak")
    if not os.path.isfile(backup):
        shutil.copy2(original, backup)
        os.utime(backup, None)  # set mtime to current time
    _atomic_replace(modified, original)


def _mutate_and_dump(assets_path, mutations, out_dir):
    """Apply (char_name, RGBA image) mutations inside one UnityPy environment,
    write the dump, then release every handle so the caller can safely
    os.replace the game file on Windows afterwards."""
    env = UnityPy.load(assets_path)
    targets = set()
    obj = d = None
    try:
        for name, img in mutations:
            obj, d = _find_texture(env, name)
            if obj is None:
                raise PhotoPackError("Character \u201c%s\u201d missing in the game." % name)
            sheet = _prep_sheet(img, d.image.size[0], d.image.size[1])
            d.image = sheet
            d.save()
            targets.add(("Texture2D", obj.path_id))
        output = _write_env_dump(env, out_dir or OUT_DIR)
    finally:
        obj = d = None
        del env
    gc.collect()
    return output, targets


def _apply_mutations(assets_path, mutations, out_dir=None):
    if not os.path.isfile(assets_path):
        raise PhotoPackError("Game file not found:\n%s\n(Set it in Settings.)" % assets_path)
    if not mutations:
        raise PhotoPackError("No matching character images to apply.")
    output, targets = _mutate_and_dump(assets_path, mutations, out_dir)
    ok, changed = _verify_objects(assets_path, output, targets)
    if not ok:
        raise PhotoPackError("Verification failed: %d objects changed (expected: %d)\n"
                             "The game file was NOT modified." % (len(changed), len(targets)))
    _commit_modified(assets_path, output)
    return len(targets)


def apply_photo_to_file(assets_path, char_name, img, status=None, out_dir=None):
    if status:
        status("Injection \u2026")
    return _apply_mutations(assets_path, [(char_name, img)], out_dir)


def apply_zip_to_file(assets_path: str, zip_path: str, items: list,
                      status: Callable[[str], None] | None = None,
                      out_dir: str | None = None) -> int:
    if not os.path.isfile(assets_path):
        raise PhotoPackError("Game file not found:\n%s\n(Set it in Settings.)" % assets_path)
    if not items:
        raise PhotoPackError("No matching character images to apply.")
    z = _open_zip(zip_path)
    try:
        # Security gate: bomb limits first, then re-validate the exact
        # members that are about to be read (zip-slip, symlinks, reserved
        # Windows names, realpath escape against the destination folder).
        _validate_zip_archive(z)
        extract_root = out_dir or OUT_DIR
        bad = []
        for _name, member in items:
            try:
                inf = z.getinfo(member)
            except KeyError:
                bad.append((member, "missing from the archive"))
                continue
            problem = _zip_member_problem(inf, extract_root)
            if problem:
                bad.append((member, problem))
        if bad:
            for member, problem in bad:
                logger.warning("Rejected ZIP member %r (%s)", member, problem)
            raise PhotoPackError(
                "The ZIP contains blocked entries:\n%s"
                % "\n".join("%s \u2014 %s" % (m, p) for m, p in bad))
        prepared, errors = _collect_zip_images(z, items, status)
    finally:
        z.close()
    if errors:
        raise PhotoPackError("\n".join(str(e) for e in errors))
    return _apply_mutations(assets_path, list(prepared.items()), out_dir)


def log_mod(kind, detail=None, n=None):
    hist = mod_history()
    hist.setdefault("applied", []).append({"ts": time_str(), "kind": kind, "detail": detail, "n": n})
    del hist["applied"][:-1000]
    try:
        ensure_data_dirs()
        with io.open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(hist, f, ensure_ascii=False, indent=1)
    except Exception:
        pass


def time_str():
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def file_mtime_str(path):
    import datetime
    try:
        return datetime.datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "?"


def file_md5(path):
    h = hashlib.md5()
    with io.open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------- detection

def steam_libraries(vdf):
    libs = []
    try:
        with io.open(vdf, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        for m in re.finditer(r'"path"\s+"([^"]+)"', text):
            libs.append(m.group(1))
    except Exception:
        pass
    return libs


def _append_candidate(folder, found):
    for sub in ("Data", DATA_DIR_NAME):
        p = os.path.join(folder, sub, ASSETS_NAME)
        if os.path.isfile(p) and p not in found:
            found.append(p)


def find_candidate_files():
    found = []

    def add(p):
        if p and os.path.isfile(p) and p not in found:
            found.append(p)

    appdir = os.path.dirname(os.path.abspath(__file__))
    for base in (appdir, os.getcwd()):
        _append_candidate(base, found)

    local_appdata = os.environ.get("LOCALAPPDATA", "")
    if local_appdata:
        for v in GAME_DIR_VARIANTS:
            _append_candidate(os.path.join(local_appdata, "Games", v), found)

    for p in (r"C:\Program Files (x86)\Steam", r"C:\Program Files\Steam"):
        if os.path.isdir(p):
            for lib in steam_libraries(os.path.join(p, "steamapps", "libraryfolders.vdf")):
                for v in GAME_DIR_VARIANTS:
                    _append_candidate(os.path.join(lib, "steamapps", "common", v), found)

    roots = []
    ev = os.path.expanduser("~")
    for k in ("Desktop", "Downloads", "Documents", "Games"):
        roots.append(os.path.join(ev, k))
    for k in roots:
        shallow_scan(k, found, depth=3)

    for letter in "CDEFGH":
        root = "%s:\\" % letter
        if os.path.isdir(root):
            deep_scan(root, found, depth=5)
    return found


def _collect_from_dir(data_dir, found):
    p = os.path.join(data_dir, ASSETS_NAME)
    if os.path.isfile(p) and p not in found:
        found.append(p)
    for sub in ("Data", DATA_DIR_NAME):
        p = os.path.join(data_dir, sub, ASSETS_NAME)
        if os.path.isfile(p) and p not in found:
            found.append(p)


def shallow_scan(top, found, depth=3):
    if not os.path.isdir(top):
        return
    stack = [(top, 0)]
    visited = 0
    while stack and visited < 40000:
        p, d = stack.pop(0)
        if d > depth:
            continue
        visited += 1
        try:
            entries = list(os.scandir(p))
        except Exception:
            continue
        for e in entries:
            try:
                if not e.is_dir(follow_symlinks=False):
                    continue
            except Exception:
                continue
            n = e.name.lower()
            if _norm_dirname(n) in _TARGET_NORMS:
                _collect_from_dir(e.path, found)
                continue
            if n[:1] in (".", "$") or n in ("windows", "system volume information", "node_modules", "temp", "cache",
                                             "program files", "program files (x86)"):
                continue
            stack.append((e.path, d + 1))


def deep_scan(root, found, depth=5):
    stack = [(root, 0)]
    visited = 0
    while stack and visited < 260000:
        p, d = stack.pop(0)
        if d > depth:
            continue
        visited += 1
        try:
            entries = list(os.scandir(p))
        except Exception:
            continue
        for e in entries:
            try:
                if e.is_dir(follow_symlinks=False):
                    n = e.name.lower()
                    if _norm_dirname(n) in _TARGET_NORMS:
                        _collect_from_dir(e.path, found)
                        continue
                    if n[:1] not in (".", "$") and n not in ("windows", "system volume information",
                                                             "node_modules", "$recycle.bin"):
                        stack.append((e.path, d + 1))
            except Exception:
                continue


# ---------------------------------------------------------------- app

class App:
    def __init__(self, root):
        self.root = root
        root.title(APP_NAME)
        root.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        _apply_tk_scaling(root)
        self._refresh_icon()
        self.root.after(120, self._refresh_icon)
        self.root.after(900, self._refresh_icon)

        self.q = queue.Queue()
        self.busy = False
        if not ensure_data_dirs():
            root.after(400, lambda: messagebox.showwarning(
                "Data folder", "The data folder could not be written:\n%s\n\n"
                "Move the app/exe to a writable location (for example your Desktop) and restart."
                % DATA_DIR))
        # load_prefs can surface t()-based messages (corrupt/corrected
        # settings) before the saved language is known, so seed the
        # default language first; the line below re-applies the choice.
        load_language(KNOWN_LANGUAGES[0])
        self.prefs = self.load_prefs()
        load_language(self.prefs.get("language", "en"))
        self.assets_path = str(self.prefs.get("assets", "") or "")
        self.photo_dir = str(self.prefs.get("photo_dir", "") or "") or os.path.expanduser("~")
        try:
            self.zoom = float(self.prefs.get("zoom", 1.0))
        except (TypeError, ValueError):
            self.zoom = 1.0
        self.zoom = max(ZOOM_MIN, min(ZOOM_MAX, self.zoom))

        self.pages = {}
        self.current_page = None

        self.textures = []
        self.images = {}
        self.cards = {}
        self.image_refs = []
        self.visible_names = []
        self.selected = None
        self.photo_image = None
        self.photo_path = None
        self.wheel_id = None
        self.filter_job = None
        self.layout_job = None
        self.zoom_job = None
        self.zoom_batch_id = 0
        self.zoom_rdr_pending = False

        self.zip_file = None
        self.zip_matches = []
        self.zip_skipped = []

        self.build_shell()
        self._apply_window_geometry()
        prefs_warning = getattr(self, "_settings_warning", None)
        if prefs_warning is not None:
            # Surface settings-correction warnings only after the shell is
            # built: a modal dialog here would otherwise show a window that is
            # still empty behind it.
            self._settings_warning = None
            self.root.after(400, lambda: messagebox.showwarning(prefs_warning[0],
                                                                prefs_warning[1]))
        self.root.after(100, self.drain_messages)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.report_callback_exception = self.report_callback_exception
        if self.assets_path and os.path.isfile(self.assets_path):
            self.set_game_file(self.assets_path, [])
        else:
            self.root.after(300, self.auto_detect)
        logger.info("App started v%s; game file: %s", APP_VERSION,
                    self.assets_path or "(not set yet)")

    # ---------------- settings json ----------------
    def load_prefs(self, quiet: bool = False):
        """Load settings.json, backing up corrupt files and validating the rest.

        quiet=True (used by save_pref) only logs; the startup path stores a
        single consolidated warning message (in ``self._settings_warning``)
        that ``App.__init__`` surfaces after the shell is built, so the main
        window is never shown empty behind the modal dialog.
        """
        try:
            ensure_data_dirs()
            with io.open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.warning("settings JSON is corrupt (%s); backing up and resetting", e)
            backup_path = "%s.bak.%s" % (SETTINGS_FILE, time.strftime("%Y%m%d-%H%M%S"))
            try:
                os.replace(SETTINGS_FILE, backup_path)
            except Exception as ex:
                logger.warning("could not rename corrupt settings file: %s", ex)
            if not quiet:
                self._settings_warning = (t("settings.dialog_title"),
                                          t("settings.corrupt_reset") % backup_path)
            return dict(DEFAULT_SETTINGS)
        except Exception as e:
            logger.warning("could not read settings file: %s", e)
            return dict(DEFAULT_SETTINGS)
        validated, warnings = validate_settings(data)
        if warnings:
            logger.warning("settings corrected: %s", "; ".join(warnings))
            if not quiet:
                self._settings_warning = (t("settings.dialog_title"),
                                          t("settings.corrected") % "\n".join(warnings))
        return validated

    def save_pref(self, key, value):
        try:
            ensure_data_dirs()
            a = self.load_prefs(quiet=True)
            a[key] = value
            with io.open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(a, f, ensure_ascii=False, indent=2)
            self.prefs = a
        except Exception as _e:
            import traceback
            traceback.print_exc()
            log_exception("save_pref FAILED: %s" % _e)

    # ---------------- misc ----------------
    def report_callback_exception(self, exc, val, tb):
        log_exception("UI callback error")
        try:
            messagebox.showerror("Unexpected error",
                                 "Something went wrong.\n\n%s" % val)
        except Exception:
            pass

    def on_close(self):
        if getattr(self, "busy", False):
            if not messagebox.askyesno("Exit",
                                       "An operation is still running.\n"
                                       "Closing now may leave the game file in the middle state.\n\n"
                                       "Wait a moment and exit anyway?"):
                return
        self._save_window_geometry()
        self.root.destroy()

    def _apply_window_geometry(self) -> None:
        """Restore the saved window size/position, centering the window when
        the saved position is offscreen or absent."""
        saved = str(self.prefs.get("window.geometry") or "")
        try:
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()
        except tk.TclError:
            screen_w, screen_h = 0, 0
        if saved and not _geometry_offscreen(saved, screen_w, screen_h):
            self.root.geometry(saved)
            return
        if saved:
            self.root.geometry(_geometry_size_only(saved))
        else:
            self.root.geometry(DEFAULT_WINDOW_GEOMETRY)
        self.root.update_idletasks()
        try:
            w = self.root.winfo_width()
            h = self.root.winfo_height()
            x = max(0, (screen_w - w) // 2)
            y = max(0, (screen_h - h) // 2)
            self.root.geometry("%dx%d+%d+%d" % (w, h, x, y))
        except tk.TclError:
            pass

    def _save_window_geometry(self) -> None:
        """Persist the current window geometry; drop the position when it
        falls outside the visible screen, keeping only the size."""
        try:
            geo = self.root.geometry()
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()
            if _geometry_offscreen(geo, screen_w, screen_h):
                geo = _geometry_size_only(geo)
            self.save_pref("window.geometry", geo)
        except Exception as e:
            logger.debug("could not save window geometry: %s", e)

    # ---------------- icon ----------------
    def _refresh_icon(self):
        try:
            ico = self._find_icon()
            if ico:
                self.root.iconbitmap(ico)
                img = Image.open(ico).convert("RGBA")
                self._title_icon = ImageTk.PhotoImage(
                    img.resize((32, 32), Image.LANCZOS)
                )
                self._title_icon16 = ImageTk.PhotoImage(
                    img.resize((16, 16), Image.LANCZOS)
                )
                self.root.iconphoto(
                    True, self._title_icon, self._title_icon16
                )
        except Exception:
            pass

    @staticmethod
    def _find_icon():
        for base in (BUNDLE_DIR, PROJECT_DIR):
            p = os.path.join(base, "NHModTool.ico")
            if os.path.isfile(p):
                return p
        return None

    # ---------------- shell ----------------
    def build_shell(self):
        leaf = ttkb.Frame(self.root)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        leaf.grid(row=0, column=0, sticky="nsew")

        menu = ttkb.Frame(leaf, width=200)
        menu.pack(side=tk.LEFT, fill=tk.Y)
        menu.pack_propagate(False)

        # ============================================================
        # SIDEBAR LOGO ALANI
        # ============================================================
        logo_frame = ttkb.Frame(menu)
        logo_frame.pack(fill=tk.X, padx=16, pady=(18, 8))
        ttkb.Label(logo_frame, text=APP_NAME,
                   font=("Segoe UI", 14, "bold"),
                   foreground=PALETTE["text.primary"]).pack(anchor=tk.W)
        ttkb.Label(logo_frame, text="No, I'm not a Human",
                   font=("Segoe UI", 9),
                   foreground=PALETTE["text.muted"]).pack(anchor=tk.W, pady=(2, 0))

        ttkb.Separator(menu).pack(fill=tk.X, padx=12, pady=(4, 8))

        # ============================================================
        # MENÜ BUTON STİLLERİ — Etkileyici Modern
        # Aktif: bg.surface + 3px accent bar + bold text.primary + accent icon
        # Pasif: transparent + text.secondary + muted icon
        # Hover: bg.surface + text.primary
        # Tüm öğeler aynı yükseklik: padding=(20, 10), anchor="w"
        # ============================================================
        _ms = ttkb.Style()
        self._menu_bg = _ms.lookup("TFrame", "background") or PALETTE["bg.base"]

        _ms.configure("SidebarPassive.TButton",
                      background=self._menu_bg,
                      foreground=PALETTE["text.secondary"],
                      borderwidth=0, relief="flat", anchor="w",
                      padding=(20, 10), font=("Segoe UI", 10))
        _ms.map("SidebarPassive.TButton",
                background=[("active", PALETTE["bg.surface"])],
                foreground=[("active", PALETTE["text.primary"])])

        _ms.configure("SidebarActive.TButton",
                      background=PALETTE["bg.surface"],
                      foreground=PALETTE["text.primary"],
                      borderwidth=0, relief="flat", anchor="w",
                      padding=(20, 10), font=("Segoe UI", 11, "bold"))
        _ms.map("SidebarActive.TButton",
                background=[("active", PALETTE["bg.surface"])],
                foreground=[("active", PALETTE["text.primary"])])

        _menu_icons = {"home": "\U0001F3E0", "photos": "\U0001F4F7", "bulk": "\U0001F4E6",
                       "manager": "\U0001F527", "status": "\U0001F4CA", "settings": "\u2699\uFE0F"}
        self.menu_buttons = {}
        self.menu_bars = {}
        for page_id, label in (("home", t("menu.home")), ("photos", t("menu.photos")), ("bulk", t("menu.photo_pack")),
                               ("manager", t("menu.manager")), ("status", t("menu.status")), ("settings", t("menu.settings"))):
            row = ttkb.Frame(menu)
            row.pack(fill=tk.X, padx=8, pady=2)  # 4px spacing (2+2)
            bar = tk.Frame(row, width=3, bg=self._menu_bg, highlightthickness=0)
            bar.pack(side=tk.LEFT, fill=tk.Y)
            btn = ttkb.Button(row, text="%s  %s" % (_menu_icons[page_id], label),
                              style="SidebarPassive.TButton",
                              command=lambda s=page_id: self.show_page(s))
            btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.menu_buttons[page_id] = btn
            self.menu_bars[page_id] = bar

        # ============================================================
        # SIDEBAR FOOTER — Yeşil nokta + "Oyun bulundu" / S1VRA branding
        # ============================================================
        ttkb.Separator(menu).pack(fill=tk.X, padx=12, pady=(8, 8))
        footer_frame = ttkb.Frame(menu)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=16, pady=(0, 16))
        self.menu_dot = ttkb.Label(footer_frame, text="\u25CF",
                                   foreground=PALETTE["state.success"], font=("Segoe UI", 8))
        self.menu_dot.pack(side=tk.LEFT, padx=(0, 6))
        self.menu_status = ttkb.Label(footer_frame, text="",
                                      font=("Segoe UI", 9),
                                      foreground=PALETTE["text.secondary"])
        self.menu_status.pack(side=tk.LEFT)

        self.content = ttkb.Frame(leaf)
        self.content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # ============================================================
        # MAIN FOOTER
        # ============================================================
        footer = ttkb.Frame(leaf)
        footer.pack(side=tk.BOTTOM, fill=tk.X)
        ttkb.Separator(footer).pack(fill=tk.X, pady=(0, 4))

        footer_inner = ttkb.Frame(footer)
        footer_inner.pack(fill=tk.X, padx=16, pady=8)

        self.footer_dot = ttkb.Label(footer_inner, text="\u25CF",
                                     foreground=PALETTE["state.success"], font=("Segoe UI", 8))
        self.footer_dot.pack(side=tk.LEFT, padx=(0, 6))
        self.footer_status = ttkb.Label(footer_inner, text="",
                                        font=("Segoe UI", 9),
                                        foreground=PALETTE["text.secondary"])
        self.footer_status.pack(side=tk.LEFT)

        self.loader_lbl = ttkb.Label(footer_inner, text="",
                                     font=("Segoe UI", 8),
                                     foreground=PALETTE["text.muted"],
                                     anchor=tk.W)
        self.loader_lbl.pack(side=tk.LEFT, padx=(12, 0))
        ttkb.Label(footer_inner, text="S1VRA \u00B7 %s v%s" % (APP_NAME, APP_VERSION),
                   font=("Segoe UI", 9),
                   foreground=PALETTE["text.muted"],
                   anchor=tk.E).pack(side=tk.RIGHT)

        self.pages["home"] = self.create_home(self.content)
        self.pages["photos"] = self.create_photos(self.content)
        self.pages["bulk"] = self.create_zip_page(self.content)
        self.pages["manager"] = self.create_manager(self.content)
        self.pages["status"] = self.create_status(self.content)
        self.pages["settings"] = self.create_settings(self.content)
        self.show_page("home")

    def show_page(self, s):
        if self.current_page == s:
            return
        if self.current_page:
            self.pages[self.current_page].pack_forget()
        self.current_page = s
        self.pages[s].pack(fill=tk.BOTH, expand=True)
        for page_id, btn in self.menu_buttons.items():
            active = page_id == s
            btn.configure(style="SidebarActive.TButton" if active else "SidebarPassive.TButton")
            self.menu_bars[page_id].config(bg=(PALETTE["accent.primary"] if active else self._menu_bg))
        self.root.after(50, self.on_page_shown, s)

    def on_page_shown(self, s):
        if s == "photos":
            self._sync_photos_empty_state()
            self.root.update_idletasks()
            if self.cards:
                self.refresh_gallery()
        elif s == "home":
            self.refresh_home()
        elif s == "manager":
            self.refresh_backup_list()
        elif s == "status":
            self.refresh_status_page()
        elif s == "bulk":
            self._sync_zip_empty_state()
            self.refresh_zip_info()

    # ---------------- page helpers ----------------
    def _fresh_page(self, parent):
        f = tk.Frame(parent, bg=COLORS["bg"])
        return f

    def _page_shell(self, parent, title, subtitle=None):
        f = ttk.Frame(parent, style="Kart.TFrame")
        f.pack(fill=tk.BOTH, expand=True, padx=18, pady=14)
        ttk.Label(f, text=title, style="Baslik.TLabel").pack(anchor=tk.W, padx=14, pady=(12, 0))
        if subtitle:
            ttk.Label(f, text=subtitle, style="Altbaslik.TLabel").pack(anchor=tk.W, padx=14, pady=(2, 0))
        ic = tk.Frame(f, bg=COLORS["card"])
        ic.pack(fill=tk.BOTH, expand=True, padx=14, pady=10)
        return f, ic

    def create_home(self, parent):
        page = self._fresh_page(parent)
        f = ttkb.Frame(page)
        f.pack(fill=tk.BOTH, expand=True, padx=24, pady=20)

        # ============================================================
        # HEADER — Etkileyici tipografi hiyerarşisi
        # ============================================================
        header = ttkb.Frame(f)
        header.pack(fill=tk.X, pady=(0, 12))

        # Sol: Uygulama adı + versiyon badge
        left_header = ttkb.Frame(header)
        left_header.pack(side=tk.LEFT)
        ttkb.Label(left_header, text=APP_NAME,
                   font=("Segoe UI", 22, "bold"),
                   foreground=PALETTE["text.primary"]).pack(side=tk.LEFT)
        # Versiyon badge: bg.surface + padding (8, 3)
        version_badge = ttkb.Frame(left_header, style="HomeCardInner.TFrame")
        version_badge.pack(side=tk.LEFT, padx=(12, 0), pady=(4, 0))
        ttkb.Label(version_badge, text="v" + APP_VERSION,
                   font=("Segoe UI", 11),
                   foreground=PALETTE["text.muted"],
                   background=PALETTE["bg.surface"]).pack(padx=8, pady=3)

        # Sağ: boşluk (gelecekte kullanıcı adı vb. için)
        # right_header = ttkb.Frame(header)
        # right_header.pack(side=tk.RIGHT)

        # Ince ayırıcı
        ttkb.Separator(f).pack(fill=tk.X, pady=(0, 20))

        # Hoş Geldiniz + açıklama
        ttkb.Label(f, text=t("home.welcome"),
                   font=("Segoe UI", 16, "bold"),
                   foreground=PALETTE["text.primary"]).pack(anchor=tk.W)
        ttkb.Label(f, text=t("home.desc"),
                   font=("Segoe UI", 10),
                   foreground=PALETTE["text.secondary"],
                   wraplength=880, justify=tk.LEFT).pack(anchor=tk.W, pady=(4, 0))

        # ============================================================
        # İÇERİK GRID — 2 kolon (sol %65, sağ %35), 2 satır
        # ============================================================
        ic = ttkb.Frame(f)
        ic.pack(fill=tk.BOTH, expand=True)

        self.home_content = tk.Frame(ic, bg=COLORS["card"])
        self.home_content.pack(fill=tk.BOTH, expand=True)
        self.home_content.grid_columnconfigure(0, weight=65)
        self.home_content.grid_columnconfigure(1, weight=35)
        self.home_content.grid_rowconfigure(0, weight=0)  # üst kartlar içeriğe göre
        self.home_content.grid_rowconfigure(1, weight=1)  # 4 kart grid'i kalan alanı doldursun
        self.home_content.grid_rowconfigure(2, weight=0)  # tip şeridi

        # ---- Stil tanımları (create_home içinde tek seferde) ----
        _st = ttkb.Style()

        # Buton stilleri
        _st.configure("danger.TButton",
                      background=PALETTE["state.danger_solid"],
                      foreground=PALETTE["text.primary"], borderwidth=0)
        _st.map("danger.TButton",
                background=[("active", PALETTE["state.danger_solid"]),
                            ("pressed", PALETTE["state.danger_solid"])],
                foreground=[("active", PALETTE["text.primary"]),
                            ("pressed", PALETTE["text.primary"])])

        _st.configure("ActionPrimary.TButton",
                      background=PALETTE["accent.primary"],
                      foreground=PALETTE["text.primary"],
                      borderwidth=0, font=("Segoe UI", 11, "bold"))
        _st.map("ActionPrimary.TButton",
                background=[("active", PALETTE["accent.hover"]),
                            ("pressed", PALETTE["accent.pressed"])],
                foreground=[("active", PALETTE["text.primary"]),
                            ("pressed", PALETTE["text.primary"])])

        _st.configure("ActionSecondary.TButton",
                      background=PALETTE["bg.surface"],
                      foreground=PALETTE["text.primary"],
                      bordercolor=PALETTE["border.subtle"], borderwidth=1,
                      font=("Segoe UI", 11))
        _st.map("ActionSecondary.TButton",
                background=[("active", PALETTE["bg.elevated"]),
                            ("pressed", PALETTE["bg.elevated"])],
                foreground=[("active", PALETTE["text.primary"]),
                            ("pressed", PALETTE["text.primary"])])

        # Kart stilleri
        _st.configure("HomeCard.TFrame", borderwidth=1, relief="solid",
                      bordercolor=PALETTE["border.subtle"], background=PALETTE["bg.surface"])
        _st.configure("HomeCardHot.TFrame", borderwidth=1, relief="solid",
                      bordercolor=PALETTE["accent.primary"], background=PALETTE["bg.surface"])
        _st.configure("HomeCardInner.TFrame", background=PALETTE["bg.surface"])
        _st.configure("HomeCardLabel.TLabel", background=PALETTE["bg.surface"])

        # ============================================================
        # SOL KOLON — Oyun Durumu Kartı (büyük, dikkat çekici)
        # ============================================================
        status_card = ttkb.Frame(self.home_content, style="HomeCard.TFrame", padding=24)
        status_card.grid(row=0, column=0, sticky="new", padx=(0, 8), pady=(0, 16))
        status_card.grid_columnconfigure(1, weight=1)

        # Sol: Büyük oyun ikonu (🎮) — transparan arka plan, yeşil renk
        self.home_status_icon = ttkb.Label(status_card, text="\U0001F3AE",  # 🎮
                                           font=("Segoe UI Emoji", 28),
                                           foreground=PALETTE["state.success"],
                                           background=PALETTE["bg.surface"])
        self.home_status_icon.grid(row=0, column=0, rowspan=3, sticky="n", padx=(0, 16), pady=(0, 4))

        # Yanında: Başlık + alt bilgi + yol
        self.home_status = ttkb.Label(status_card, text="",
                                      font=("Segoe UI", 18, "bold"),
                                      foreground=PALETTE["text.primary"],
                                      background=PALETTE["bg.surface"],
                                      anchor=tk.W)
        self.home_status.grid(row=0, column=1, sticky="w", pady=(0, 2))

        self.home_file = ttkb.Label(status_card, text="",
                                    font=("Segoe UI", 11),
                                    foreground=PALETTE["text.secondary"],
                                    background=PALETTE["bg.surface"],
                                    anchor=tk.W)
        self.home_file.grid(row=1, column=1, sticky="w", pady=(0, 4))

        self.home_path = ttkb.Label(status_card, text="",
                                    font=("Segoe UI", 9),
                                    foreground=PALETTE["text.muted"],
                                    background=PALETTE["bg.surface"],
                                    anchor=tk.W, justify=tk.LEFT,
                                    wraplength=520)
        self.home_path.grid(row=2, column=1, sticky="w")

        # ============================================================
        # SAĞ KOLON — Aksiyon Butonları
        # ============================================================
        action_card = ttkb.Frame(self.home_content, style="HomeCard.TFrame", padding=16)
        action_card.grid(row=0, column=1, sticky="new", padx=(8, 0), pady=(0, 16))
        action_card.grid_columnconfigure(0, weight=1)

        # Buton yardımcı fonksiyonu (ikon + metin)
        def make_btn(parent, text, icon, style, cmd, row):
            btn_frame = ttkb.Frame(parent, style="HomeCardInner.TFrame")
            btn_frame.grid(row=row, column=0, sticky="ew", pady=5)
            btn = ttkb.Button(btn_frame, text=f" {icon}  {text}",
                              style=style, command=cmd)
            btn.pack(fill=tk.X, ipady=6)
            return btn

        make_btn(action_card, t("home.open_game_folder"), "\U0001F4C1",  # 📁
                 "ActionPrimary.TButton",
                 lambda: self.open_path(os.path.dirname(self.assets_path) if self.assets_path else PROJECT_DIR), 0)
        make_btn(action_card, t("home.restore_backup"), "\u21BA",  # ↺
                 "ActionSecondary.TButton", self.restore_backup, 1)
        make_btn(action_card, t("home.clear_cache"), "\U0001F5D1",  # 🗑
                 "danger.TButton", self.clear_cache, 2)
        make_btn(action_card, t("home.data_folder") + "\u2026", "\U0001F4C1",  # 📁
                 "ActionSecondary.TButton", lambda: self.open_path(DATA_DIR), 3)

        # ============================================================
        # ALT GRID — 4 Büyük Kart (2x2)
        # ============================================================
        card_grid = ttkb.Frame(self.home_content)
        card_grid.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(8, 0))
        card_grid.grid_columnconfigure(0, weight=1)
        card_grid.grid_columnconfigure(1, weight=1)
        card_grid.grid_rowconfigure(0, minsize=160, weight=1)
        card_grid.grid_rowconfigure(1, minsize=160, weight=1)

        cards = ((t("home.photo_mods"), "\U0001F4F7", t("home.photo_mods_desc"), "photos"),
                 (t("home.photo_pack"), "\U0001F4E6", t("home.photo_pack_desc"), "bulk"),
                 (t("home.mod_manager"), "\U0001F527", t("home.mod_manager_desc"), "manager"),
                 (t("home.game_status"), "\U0001F4CA", t("home.game_status_desc"), "status"))

        def _make_wire(w, page_id, card, chev_lbl):
            w.bind("<Button-1>", lambda e, s=page_id: self.show_page(s))
            w.bind("<Enter>", lambda e, c=card, ch=chev_lbl: (
                c.configure(style="HomeCardHot.TFrame"),
                ch.configure(foreground=PALETTE["accent.primary"])
            ))
            w.bind("<Leave>", lambda e, c=card, ch=chev_lbl: (
                c.configure(style="HomeCard.TFrame"),
                ch.configure(foreground=PALETTE["text.muted"])
            ))

        for i, (title, icon, desc, page_id) in enumerate(cards):
            card = ttkb.Frame(card_grid, style="HomeCard.TFrame", padding=24, cursor="hand2")
            card.grid(row=i // 2, column=i % 2, sticky="nsew", padx=8, pady=8)
            card.grid_propagate(False)

            # Üst satır: İkon + Başlık + Chevron
            top_row = ttkb.Frame(card, style="HomeCardInner.TFrame")
            top_row.pack(fill=tk.X)
            top_row.grid_columnconfigure(1, weight=1)

            icon_lbl = ttkb.Label(top_row, text=icon,
                                  font=("Segoe UI Emoji", 22),
                                  foreground=PALETTE["text.primary"],
                                  background=PALETTE["bg.surface"])
            icon_lbl.grid(row=0, column=0, sticky="w", padx=(0, 12))

            title_lbl = ttkb.Label(top_row, text=title,
                                   font=("Segoe UI", 14, "bold"),
                                   foreground=PALETTE["text.primary"],
                                   background=PALETTE["bg.surface"],
                                   anchor=tk.W)
            title_lbl.grid(row=0, column=1, sticky="w")

            chev_lbl = ttkb.Label(top_row, text="\u203A",  # ›
                                  font=("Segoe UI", 20),
                                  foreground=PALETTE["text.muted"],
                                  background=PALETTE["bg.surface"])
            chev_lbl.grid(row=0, column=2, sticky="e")

            # Açıklama
            desc_lbl = ttkb.Label(card, text=desc,
                                  font=("Segoe UI", 10),
                                  foreground=PALETTE["text.secondary"],
                                  background=PALETTE["bg.surface"],
                                  anchor=tk.W, justify=tk.LEFT,
                                  wraplength=380)
            desc_lbl.pack(fill=tk.X, pady=(10, 0))

            # Tıklama/hover wiring
            for w in (card, top_row, icon_lbl, title_lbl, desc_lbl):
                w.configure(cursor="hand2")
                _make_wire(w, page_id, card, chev_lbl)

        # ============================================================
        # İPUCU ŞERİDİ
        # ============================================================
        tip_lbl = ttkb.Label(self.home_content, text=t("home.tip"),
                             font=("Segoe UI", 9),
                             foreground=PALETTE["text.muted"],
                             background=PALETTE["bg.surface"],
                             anchor=tk.W, justify=tk.LEFT,
                             wraplength=880)
        tip_lbl.grid(row=2, column=0, columnspan=2, sticky="ew", padx=0, pady=(16, 0))

        self.home_empty = _build_empty_state(
            ic, "home.empty.title", "home.empty.body", "home.empty.action",
            self.browse_assets, icon="\U0001F3AE")
        self._sync_home_empty_state()
        return page

    def _sync_home_empty_state(self) -> None:
        """Show the empty-state frame when no game file is set; otherwise
        show the populated home content."""
        if not hasattr(self, "home_empty"):
            return
        game_ok = bool(self.assets_path and os.path.isfile(self.assets_path))
        if game_ok:
            self.home_empty.pack_forget()
            self.home_content.pack(fill=tk.BOTH, expand=True)
        else:
            self.home_content.pack_forget()
            self.home_empty.pack(fill=tk.BOTH, expand=True)

    def refresh_home(self):
        self._sync_home_empty_state()
        if self.assets_path and os.path.isfile(self.assets_path):
            size = os.path.getsize(self.assets_path) // (1024 * 1024)
            # Oyun bulundu durumu
            self.home_status.config(text=t("status.game_found").replace("\u2713", "").strip())
            self.home_file.config(text="%s   \u00B7  %d MB" % (os.path.basename(self.assets_path), size))
            self.home_path.config(text=self.assets_path)
            self.home_status_icon.config(foreground=PALETTE["state.success"])
            self.menu_status.config(text=t("status.game_found"))
            self.menu_dot.config(foreground=PALETTE["state.success"])
            self.footer_dot.config(foreground=PALETTE["state.success"])
            self.footer_status.config(text=t("status.game_found"))
            self.footer_dot.pack(side=tk.LEFT, padx=(0, 6))
            self.footer_status.pack(side=tk.LEFT)
            self.loader_lbl.config(text=t("status.game_found"))
            try:
                if hasattr(self, "_game_badge"):
                    self._game_badge.destroy()
                self._game_badge = tk.Frame(self.menu_status, bg=COLORS["ok"], width=8, height=8, relief=tk.RAISED, borderwidth=1)
                self._game_badge.place(x=self.menu_status.winfo_width() - 18, y=2)
            except Exception:
                pass
        else:
            self.home_status.config(text=t("status.scanning_long"))
            self.home_file.config(text="")
            self.home_path.config(text="")
            self.home_status_icon.config(foreground=PALETTE["text.muted"])
            self.menu_status.config(text=t("status.scanning"))
            self.menu_dot.config(foreground=PALETTE["state.warning"])
            self.footer_dot.pack_forget()
            self.footer_status.pack_forget()
            self.loader_lbl.config(text=t("status.scanning"))

    def open_path(self, path):
        try:
            os.startfile(path)
        except Exception as e:
            messagebox.showerror("Error", "Could not open:\n%s\n%s" % (path, e))

    def clear_cache(self):
        if not is_under_managed_root(CACHE_ROOT, MANAGED_ROOT_PATHS):
            logger.error("Security: clear_cache blocked - %s not under a managed root", CACHE_ROOT)
            messagebox.showerror(t("security.dialog_title"),
                                 t("security.delete_blocked") % CACHE_ROOT)
            return
        n = 0
        try:
            if os.path.isdir(CACHE_ROOT):
                for fn in os.listdir(CACHE_ROOT):
                    p = os.path.join(CACHE_ROOT, fn)
                    if not is_under_managed_root(p, MANAGED_ROOT_PATHS):
                        logger.error("Security: clear_cache blocked - %s not under a managed root", p)
                        messagebox.showerror(t("security.dialog_title"),
                                             t("security.delete_blocked") % p)
                        return
                    if os.path.isdir(p):
                        shutil.rmtree(p, ignore_errors=True)
                    else:
                        try:
                            os.remove(p)
                        except Exception:
                            pass
                    n += 1
        except Exception:
            log_exception("clear_cache")
        messagebox.showinfo("Cache", "Thumbnail cache cleared (%d folder(s)).\nNext gallery open re-creates it quickly."
                            % n)
        if not os.path.isdir(CACHE_ROOT) or not os.listdir(CACHE_ROOT):
            self.loader_lbl.config(text=t("status.cache_empty"))

    # ---------------- photos page ----------------
    def create_photos(self, parent):
        page = self._fresh_page(parent)
        f, ic = self._page_shell(page, "Photo Mods",
                                     "Pick a character, pick a photo, one click to apply. A verification runs before anything is written.")
        self.photos_content = tk.Frame(ic, bg=COLORS["card"])
        self.photos_content.pack(fill=tk.BOTH, expand=True)
        self.build_photos(self.photos_content)
        self.photos_empty = _build_empty_state(
            ic, "photos.empty.title", "photos.empty.body", "photos.empty.action",
            self.pick_photo, icon="\U0001F4F7")
        self._sync_photos_empty_state()
        return page

    def _sync_photos_empty_state(self) -> None:
        """Show the empty-state frame until a photo is picked; then show the
        populated photo editor content."""
        if not hasattr(self, "photos_empty"):
            return
        if self.photo_path:
            self.photos_empty.pack_forget()
            self.photos_content.pack(fill=tk.BOTH, expand=True)
        else:
            self.photos_content.pack_forget()
            self.photos_empty.pack(fill=tk.BOTH, expand=True)

    def build_photos(self, ic):
        ara = ttk.Frame(ic, style="Kart.TFrame")
        ara.pack(fill=tk.X, pady=(0, 8))
        box = tk.Frame(ara, bg=PALETTE["bg.elevated"], highlightbackground=PALETTE["border.subtle"], highlightthickness=1)
        box.pack(fill=tk.X, side=tk.LEFT, expand=True)
        self.search_var = tk.StringVar()
        tk.Label(box, text="\U0001F50D", bg=PALETTE["bg.elevated"], fg=PALETTE["text.muted"], font=(FONT, 10)).pack(side=tk.LEFT, padx=(8, 4))
        tk.Entry(box, textvariable=self.search_var, bg=PALETTE["bg.elevated"], fg=PALETTE["text.primary"], relief=tk.FLAT,
                 insertbackground=PALETTE["text.primary"], font=(FONT, 10)).pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        self.search_var.trace_add("write", lambda *a: self.filter_debounce())
        self.mask_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(ara, text=t("photos.show_masks"), variable=self.mask_var, command=self.refresh_gallery).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Separator(ara, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=2)
        ttk.Label(ara, text="\U0001F50B", style="Soluk.TLabel").pack(side=tk.LEFT, padx=(0, 2))
        ttkb.Button(ara, text="\u2212", width=2, bootstyle="secondary-outline", command=lambda: self.zoom_step(-1)).pack(side=tk.LEFT, padx=(4, 2))
        self.zoom_lbl = ttk.Label(ara, text="%d%%" % (self.zoom * 100), style="Soluk.TLabel", width=5, anchor=tk.CENTER)
        self.zoom_lbl.pack(side=tk.LEFT, padx=2)
        ttkb.Button(ara, text="+", width=2, bootstyle="secondary-outline", command=lambda: self.zoom_step(1)).pack(side=tk.LEFT, padx=2)
        ttkb.Button(ara, text="1:1", width=3, bootstyle="secondary-outline", command=self.zoom_reset).pack(side=tk.LEFT, padx=(2, 4))

        body = tk.Frame(ic, bg=PALETTE["bg.surface"])
        body.pack(fill=tk.BOTH, expand=True)

        left_pane = tk.Frame(body, bg=PALETTE["bg.surface"])
        left_pane.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        gallery_host = tk.Frame(left_pane, bg=PALETTE["bg.surface"])
        gallery_host.pack(fill=tk.BOTH, expand=True)

        # Loading indicator for gallery
        self.gallery_loading = ttk.Progressbar(gallery_host, mode="indeterminate", length=200)
        self.gallery_loading.pack(pady=10)
        self.gallery_loading_label = tk.Label(gallery_host, text="", bg=PALETTE["bg.surface"], fg=PALETTE["accent.primary"], font=(FONT, 9))
        self.gallery_loading_label.pack()
        self.gallery_loading.pack_forget()
        self.gallery_loading_label.pack_forget()

        self.canvas = tk.Canvas(gallery_host, bg=PALETTE["bg.base"], highlightthickness=0, takefocus=1)
        vbar = ttk.Scrollbar(gallery_host, orient=tk.VERTICAL, command=self._yview)
        self.canvas.configure(yscrollcommand=vbar.set)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.card_items = {}          # canvas item id -> character name
        self.empty_text = self.canvas.create_text(12, 12, text=t("photos.no_matches"), fill=PALETTE["text.muted"],
                                                   font=(FONT, 11), anchor=tk.NW, state=tk.HIDDEN)
        self.canvas.bind("<Configure>", lambda e: self.on_canvas_resize(e))
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Enter>", lambda e: self.bind_wheel())
        self.canvas.bind("<Leave>", lambda e: self.unbind_wheel())
        self.root.bind_all("<Control-plus>", lambda e: self.zoom_step(1))
        self.root.bind_all("<Control-KP_Add>", lambda e: self.zoom_step(1))
        self.root.bind_all("<Control-minus>", lambda e: self.zoom_step(-1))
        self.root.bind_all("<Control-KP_Subtract>", lambda e: self.zoom_step(-1))
        self.root.bind_all("<Control-0>", lambda e: self.zoom_reset())
        ttk.Label(left_pane, text=t("photos.resize_tip"),
                  style="Altbaslik.TLabel").pack(anchor=tk.W, pady=(8, 0))

        right_pane = tk.Frame(body, bg=PALETTE["bg.surface"], width=340)
        right_pane.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 0))
        right_pane.pack_propagate(False)

        current_panel = tk.Frame(right_pane, bg=PALETTE["bg.elevated"], highlightbackground=PALETTE["border.subtle"], highlightthickness=1)
        current_panel.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 8))
        tk.Label(current_panel, text=t("photos.in_game_current"), bg=PALETTE["bg.elevated"], fg=PALETTE["accent.primary"], font=("Segoe UI", 12, "bold"),
                 anchor=tk.W).pack(fill=tk.X, padx=10, pady=8)
        self.lbl_prev_original = tk.Label(current_panel, text=t("photos.select_hint"), bg=PALETTE["bg.elevated"],
                                          fg=PALETTE["text.secondary"], font=("Segoe UI", 10))
        self.lbl_prev_original.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 4))
        self.lbl_meta = ttk.Label(current_panel, text="", style="Muted.TLabel")
        self.lbl_meta.pack(anchor=tk.W, padx=10, pady=(0, 8))

        new_frame = tk.Frame(right_pane, bg=PALETTE["bg.elevated"], highlightbackground=PALETTE["border.subtle"], highlightthickness=1)
        new_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        tk.Label(new_frame, text=t("photos.new_image"), bg=PALETTE["bg.elevated"], fg=PALETTE["accent.primary"], font=("Segoe UI", 12, "bold"),
                 anchor=tk.W).pack(fill=tk.X, padx=10, pady=8)
        self.lbl_prev_new = tk.Label(new_frame, text=t("photos.pick_hint"), bg=PALETTE["bg.elevated"], fg=PALETTE["text.secondary"],
                                      font=("Segoe UI", 10))
        self.lbl_prev_new.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

        controls = ttk.Frame(right_pane, style="Kart.TFrame")
        controls.pack(side=tk.TOP, fill=tk.X, pady=(10, 0))
        self.photo_path_var = tk.StringVar()
        ttk.Entry(controls, textvariable=self.photo_path_var, state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        ttk.Button(controls, text="\U0001F4F7  " + t("photos.photo_browse"), style="Secondary.TButton", command=self.pick_photo).pack(side=tk.LEFT)
        self.apply_btn = ttk.Button(right_pane, text="\u2713  " + t("photos.apply_to_game"), style="ActionPrimary.TButton", command=self.apply_start,
                                    state=tk.DISABLED)
        self.apply_btn.pack(side=tk.TOP, fill=tk.X, pady=(10, 0), ipady=10, ipadx=16)

    # ---------------- zoom & gallery ----------------
    def filter_debounce(self):
        if self.filter_job is not None:
            self.root.after_cancel(self.filter_job)
        self.filter_job = self.root.after(200, self.refresh_gallery)

    def relayout(self):
        self.layout_job = None
        self.refresh_gallery()

    def on_canvas_resize(self, evt):
        if self.layout_job is None and self.cards:
            self.layout_job = self.root.after(120, self.relayout)

    def bind_wheel(self):
        def handle(evt):
            if evt.state & 0x0004:
                self.zoom_step(-1 if evt.delta > 0 else 1)
            else:
                self.canvas.yview_scroll(int(-evt.delta / 120), "units")
                self.root.after(40, self._repair_visible_cells)
        self.wheel_id = self.canvas.bind_all("<MouseWheel>", handle)

    def _yview(self, *args):
        self.canvas.yview(*args)
        self.root.after(40, self._repair_visible_cells)

    def unbind_wheel(self):
        if self.wheel_id is not None:
            self.canvas.unbind_all("<MouseWheel>")
            self.wheel_id = None

    def zoom_step(self, step):
        next_zoom = round(self.zoom + ZOOM_ADIM * step, 2)
        if next_zoom < ZOOM_MIN or next_zoom > ZOOM_MAX or next_zoom == self.zoom:
            return
        self.zoom = next_zoom
        self.zoom_lbl.config(text="%d%%" % (self.zoom * 100))
        self.save_pref("zoom", self.zoom)
        if self.zoom_job is not None:
            try:
                self.root.after_cancel(self.zoom_job)
            except Exception:
                pass
        self.zoom_job = self.root.after(150, self.zoom_render)

    def zoom_reset(self):
        self.zoom = 1.0
        self.zoom_lbl.config(text="%d%%" % (self.zoom * 100))
        self.save_pref("zoom", self.zoom)
        if self.zoom_job is not None:
            try:
                self.root.after_cancel(self.zoom_job)
            except Exception:
                pass
        self.zoom_render()

    def zoom_render(self):
        self.zoom_job = None
        if not self.textures:
            return
        self.zoom_batch_id += 1
        self.refresh_zoom_imgs()
        self.refresh_gallery()

    def refresh_zoom_imgs(self):
        task = self.zoom_batch_id
        _, _, cell_w, cell_h, label_font = self._card_metrics()
        cap_font = tkfont.Font(family=FONT, size=label_font)
        line_h = cap_font.metrics("linespace")
        for card in self.cards.values():
            dirty = card["cell_w"] != cell_w or card["cell_h"] != cell_h
            card["cell_w"] = cell_w
            card["cell_h"] = cell_h
            card["line_h"] = line_h
            card["cap_h"] = len(card["lines"]) * line_h + 6
            card["card_h"] = cell_h + card["cap_h"]
            card["label_font"] = label_font
            card["img_dirty"] = card.get("img_dirty", False) or dirty
        names = [name for name in self.visible_names if name in self.cards]
        self.zoom_cursor = 0

        def step():
            if task != self.zoom_batch_id:
                return
            end_at = min(self.zoom_cursor + 48, len(names))
            for name in names[self.zoom_cursor:end_at]:
                card = self.cards.get(name)
                if card is None or not card.get("img_dirty"):
                    continue
                src_img = self.images.get(name)
                if src_img is None:
                    continue
                try:
                    img_n = ImageTk.PhotoImage(make_cell(src_img, CHECKER_LIGHT_RGB, cell_w, cell_h))
                    img_s = ImageTk.PhotoImage(make_cell(src_img, CHECKER_DARK_RGB, cell_w, cell_h))
                except Exception:
                    continue
                card["img_n"] = img_n
                card["img_s"] = img_s
                card["img_dirty"] = False
                self.image_refs.append(img_n)
                self.image_refs.append(img_s)
                self.canvas.itemconfigure(card["img_item"],
                                          image=img_s if name == self.selected else img_n)
            self.zoom_cursor = end_at
            if end_at < len(names):
                self.root.after(16, step)
            else:
                self.zoom_rdr_pending = False

        self.zoom_rdr_pending = True
        step()

    def _repair_visible_cells(self):
        """Rebuild cell images only for visible cards whose photo is stale
        (e.g. zoomed then scrolled into view). Bounded to on-screen cards."""
        if self.zoom_rdr_pending:
            return
        try:
            _, _, cell_w, cell_h, _ = self._card_metrics()
            for name in self.visible_names:
                card = self.cards.get(name)
                if card is None or not card.get("img_dirty"):
                    continue
                src_img = self.images.get(name)
                if src_img is None:
                    continue
                try:
                    img_n = ImageTk.PhotoImage(make_cell(src_img, CHECKER_LIGHT_RGB, cell_w, cell_h))
                    img_s = ImageTk.PhotoImage(make_cell(src_img, CHECKER_DARK_RGB, cell_w, cell_h))
                except Exception:
                    continue
                card["img_n"] = img_n
                card["img_s"] = img_s
                card["img_dirty"] = False
                self.image_refs.append(img_n)
                self.image_refs.append(img_s)
                self.canvas.itemconfigure(card["img_item"],
                                          image=img_s if name == self.selected else img_n)
        except tk.TclError:
            pass

    def refresh_gallery(self):
        if self.filter_job is not None:
            try:
                self.root.after_cancel(self.filter_job)
            except Exception:
                pass
            self.filter_job = None
        needle = self.search_var.get().lower().strip()
        shown = []
        for name, w, h, fmt in self.textures:
            if needle and needle not in name.lower():
                continue
            if name.lower().endswith("_mask") and not self.mask_var.get():
                continue
            shown.append(name)
        width = max(self.canvas.winfo_width(), 300)
        card_w, _, _, _, _ = self._card_metrics()
        cols = max(1, (width + GAP) // (card_w + GAP))
        now = set(shown)
        for i, name in enumerate(shown):
            card = self.cards.get(name)
            if card is None:
                continue
            x = (i % cols) * (card_w + GAP) + GAP
            y = (i // cols) * (card["card_h"] + GAP) + GAP
            card["x"], card["y"] = x, y
            self.canvas.coords(card["sel_item"], x - 2, y - 2, x + card_w + 2, y + card["card_h"] + 2)
            self.canvas.coords(card["img_item"], x + (card_w - card["cell_w"]) // 2, y)
            self.canvas.coords(card["cap_item"], x + 6, y + card["cell_h"] + 2)
            self.canvas.itemconfigure(card["img_item"], state=tk.NORMAL)
            self.canvas.itemconfigure(card["cap_item"], state=tk.NORMAL)
            is_sel = name == self.selected
            if card.get("sel") != is_sel:
                self._style_card(card, is_sel, name)
                card["sel"] = is_sel
        for name, card in self.cards.items():
            if name in now:
                continue
            self.canvas.itemconfigure(card["img_item"], state=tk.HIDDEN)
            self.canvas.itemconfigure(card["cap_item"], state=tk.HIDDEN)
            self.canvas.itemconfigure(card["sel_item"], state=tk.HIDDEN)
            card["sel"] = False
        self.visible_names = shown
        if not shown and self.textures:
            self.canvas.coords(self.empty_text, 12, 12)
            self.canvas.itemconfigure(self.empty_text, state=tk.NORMAL)
        else:
            self.canvas.itemconfigure(self.empty_text, state=tk.HIDDEN)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self._repair_visible_cells()

    def _card_metrics(self):
        card_w = max(60, int(CARD_W * self.zoom))
        card_h = max(50, int(CARD_H * self.zoom))
        cell_w = max(52, int(CELL_W * self.zoom))
        cell_h = max(40, int(CELL_H * self.zoom))
        label_font = max(7, int(8 * self.zoom))
        return card_w, card_h, cell_w, cell_h, label_font

    def _wrap_caption(self, text, font, width):
        words = text.split()
        lines = []
        cur = ""
        for wd in words:
            test = (cur + " " + wd).strip()
            if cur and font.measure(test) > width:
                lines.append(cur)
                cur = wd
            else:
                cur = test
            if len(lines) >= 2:
                lines[-1] = lines[-1] + "\u2026"
                break
        if cur:
            lines.append(cur)
        return lines[:2] or [""]

    def _style_card(self, card, is_sel, name):
        self.canvas.itemconfigure(card["img_item"], image=card["img_s"] if is_sel else card["img_n"])
        self.canvas.itemconfigure(card["cap_item"],
                                  fill=PALETTE["text.primary"] if is_sel else PALETTE["text.primary"],
                                  font=(FONT, card["label_font"], "bold" if is_sel else "normal"))
        self.canvas.itemconfigure(card["sel_item"], state=tk.NORMAL if is_sel else tk.HIDDEN)

    def on_canvas_click(self, evt):
        x = self.canvas.canvasx(evt.x)
        y = self.canvas.canvasy(evt.y)
        hits = self.canvas.find_overlapping(x, y, x, y)
        for item_id in reversed(hits):
            name = self.card_items.get(item_id)
            if name is not None:
                self.select_card(name)
                return

    def build_cards(self):
        self.canvas.delete("card")
        self.cards = {}
        self.card_items = {}
        self.image_refs = []
        card_w, card_h, cell_w, cell_h, label_font = self._card_metrics()
        cap_font = tkfont.Font(family=FONT, size=label_font)
        line_h = cap_font.metrics("linespace")
        for name, w, h, fmt in self.textures:
            if name not in self.images:
                continue
            src_img = self.images[name]
            img_n = ImageTk.PhotoImage(make_cell(src_img, CHECKER_LIGHT_RGB, cell_w, cell_h))
            img_s = ImageTk.PhotoImage(make_cell(src_img, CHECKER_DARK_RGB, cell_w, cell_h))
            self.image_refs.append(img_n)
            self.image_refs.append(img_s)
            lines = self._wrap_caption(name, cap_font, card_w - 12)
            cap_h = len(lines) * line_h + 6
            sel_item = self.canvas.create_rectangle(0, 0, card_w, cell_h + cap_h,
                                                    outline=PALETTE["accent.primary"], width=2, state=tk.HIDDEN, tags="card")
            img_item = self.canvas.create_image(0, 0, image=img_n, anchor=tk.NW, tags="card")
            cap_item = self.canvas.create_text(0, 0, text="\n".join(lines), anchor=tk.NW,
                                               fill=PALETTE["text.primary"], font=(FONT, label_font, "normal"), tags="card")
            for item_id in (sel_item, img_item, cap_item):
                self.card_items[item_id] = name
            self.cards[name] = {"img_n": img_n, "img_s": img_s,
                                "img_item": img_item, "cap_item": cap_item, "sel_item": sel_item,
                                "cell_w": cell_w, "cell_h": cell_h, "label_font": label_font,
                                "lines": lines, "cap_h": cap_h, "card_h": cell_h + cap_h,
                                "sel": False, "x": 0, "y": 0, "img_dirty": False}
        self.refresh_gallery()

    def select_card(self, name):
        if self.selected == name:
            return
        card = self.cards.get(name)
        if card is None:
            return
        if self.selected:
            old = self.cards.get(self.selected)
            if old is not None:
                self._style_card(old, False, self.selected)
                old["sel"] = False
        self.selected = name
        self._style_card(card, True, name)
        card["sel"] = True
        meta = next((x for x in self.textures if x[0] == name), None)
        if meta:
            self.lbl_meta.config(text=t("photos.meta")
                                            % (meta[0], meta[1], meta[2], meta[3], fmt_name(meta[3])))
        if name in self.images:
            self.preview_in_label(self.lbl_prev_original, self.images[name], 320, 240)
        self.refresh_apply_state()

    def refresh_apply_state(self):
        uygun = bool(self.selected and self.photo_path)
        self.apply_btn.config(state=tk.NORMAL if uygun else tk.DISABLED)

    # ---------------- gallery data loader ----------------
    def cache_is_stale(self, cache, assets, count):
        try:
            with io.open(os.path.join(cache, "meta.txt"), "r", encoding="utf-8") as f:
                imza = f.read().strip()
            st = os.stat(assets)
            return imza != "%s_%d_%d" % (assets, st.st_size, int(st.st_mtime))
        except Exception:
            return True

    def write_cache_marker(self, cache, assets, count):
        try:
            st = os.stat(assets)
            with io.open(os.path.join(cache, "meta.txt"), "w", encoding="utf-8") as f:
                f.write("%s_%d_%d" % (assets, st.st_size, int(st.st_mtime)))
        except Exception:
            pass

    def make_thumb(self, img):
        g = img.convert("RGBA")
        g.thumbnail((THUMB_W, THUMB_H), Image.LANCZOS)
        return g

    def load_worker(self, path):
        self.q.put(("gallery_loading_start", "Loading thumbnails..."))
        try:
            env = UnityPy.load(path)
            items = []
            by_name = {}
            for obj in env.objects:
                if obj.type.name != "Texture2D":
                    continue
                try:
                    d = obj.read()
                except Exception:
                    log_exception("load_worker: obj.read")
                    continue
                name = d.m_Name or ""
                lower = name.lower()
                if not lower.startswith("fake_") or "photo" in lower:
                    continue
                items.append((name, d.m_Width, d.m_Height, d.m_TextureFormat))
                by_name[name] = obj
            items.sort(key=lambda x: x[0].lower())

            thumbs = {}
            cache = cache_dir(path)
            if self.cache_is_stale(cache, path, len(items)):
                if not is_under_managed_root(cache, MANAGED_ROOT_PATHS):
                    logger.error("Security: stale cache refresh blocked - %s not under a managed root", cache)
                    self.q.put(("status", t("security.cache_refresh_blocked")))
                else:
                    shutil.rmtree(cache, ignore_errors=True)
            os.makedirs(cache, exist_ok=True)
            missing = []
            for name, w, h, fmt in items:
                thumb_path = os.path.join(cache, safe_name(name) + ".png")
                if os.path.isfile(thumb_path):
                    try:
                        thumbs[name] = Image.open(thumb_path).convert("RGBA")
                        continue
                    except Exception:
                        pass
                missing.append(name)
            if missing:
                self.q.put(("status", "%d images prepared for the first time\u2026 (next launch will be fast)" % len(missing)))
                for name in missing:
                    obj = by_name.get(name)
                    if obj is None:
                        continue
                    try:
                        img = self.make_thumb(obj.read().image)
                    except Exception:
                        log_exception("load_worker: make_thumb %s" % name)
                        continue
                    thumbs[name] = img
                    try:
                        img.save(os.path.join(cache, safe_name(name) + ".png"))
                    except Exception:
                        log_exception("load_worker: thumb save %s" % name)
                        continue
            self.write_cache_marker(cache, path, len(items))
            self.q.put(("results", items, thumbs))
        except Exception as e:
            self.q.put(("error", "Could not read the game assets: %s" % e))
        finally:
            self.q.put(("gallery_loading_stop",))

    # ---------------- single photo injection ----------------
    def pick_photo(self):
        if self.busy:
            messagebox.showinfo("Busy", "An operation is already running. Please wait.")
            return
        y = filedialog.askopenfilename(title="Pick a photo",
                                       initialdir=self.photo_dir,
                                       filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp *.gif"), ("All files", "*.*")])
        if y:
            self.photo_dir = os.path.dirname(y)
            self.save_pref("photo_dir", self.photo_dir)
            self.photo_path_var.set(y)
            self.photo_path = y
            self.loader_lbl.config(text="")
            try:
                img = Image.open(y).convert("RGBA")
            except Exception:
                messagebox.showerror("Error", "Could not open the photo.")
                return
            self.photo_image = img
            self._preview_photo()
            self.refresh_apply_state()
            self._sync_photos_empty_state()

    def _preview_photo(self):
        """Show the selected photo preview."""
        if not self.photo_path:
            return
        src = self.photo_image
        if src is None:
            return
        self.preview_in_label(self.lbl_prev_new, src, 320, 240)

    def _checkerboard_board(self, width: int, height: int, square: int = 8) -> Image.Image:
        """Pillow checkerboard board used to composite translucent previews.

        The preview pastes the (semi-transparent) photo crop onto the board
        before converting the result into a Tk image.
        """
        img = Image.new("RGB", (width, height), CHECKER_LIGHT_RGB)
        draw = ImageDraw.Draw(img)
        for y in range(0, height, square):
            for x in range(0, width, square):
                if ((x // square) + (y // square)) % 2 == 0:
                    draw.rectangle([x, y, x + square - 1, y + square - 1], fill=CHECKER_DARK_RGB)
        return img

    def preview_in_label(self, label, img, maxg, maxy):
        copy = img.copy()
        if copy.mode == "RGBA":
            box = copy.getbbox()
            if box is None:
                box = (0, 0, copy.width, copy.height)
            w = box[2] - box[0]
            h = box[3] - box[1]
            scale = min(maxg / max(w, 1), maxy / max(h, 1))
            bw = max(int(w * scale), 1)
            bh = max(int(h * scale), 1)
            board = self._checkerboard_board(bw, bh)
            crop = copy.crop(box).resize((bw, bh), Image.LANCZOS)
            board.paste(crop, (0, 0), crop)
            tkimg = ImageTk.PhotoImage(board)
        else:
            copy.thumbnail((maxg, maxy), Image.LANCZOS)
            tkimg = ImageTk.PhotoImage(copy)
        label.config(image=tkimg, text="")
        label.image = tkimg

    def apply_start(self):
        if not self.selected or not self.photo_path:
            return
        if self.busy:
            messagebox.showinfo("Busy", "An operation is already running. Please wait.")
            return
        if not messagebox.askyesno("Apply",
                                   "Write this image into the game file?\n\n%s" % self.selected):
            return
        self.apply_btn.config(state=tk.DISABLED)
        self.busy = True
        self.status_bar.start(40)
        threading.Thread(target=self.apply_worker, daemon=True).start()

    def apply_worker(self):
        self.busy = True
        try:
            meta = next((x for x in self.textures if x[0] == self.selected), None)
            if meta is None:
                self.q.put(("error", "Selected character was not found."))
                return
            name = meta[0]
            assets = self.assets_path
            self.q.put(("status", "Preparing the photo (%dx%d target) \u2026" % (meta[1], meta[2])))
            src = self.photo_image
            self.q.put(("status", "Injection started \u2026"))
            apply_photo_to_file(assets, name, src, status=lambda t: self.q.put(("status", t)))
            log_mod("photo", name, 1)
            self.q.put(("done", "Character \u201c%s\u201d updated in the game.\n(A backup was made automatically.)" % name))
        except PhotoPackError as e:
            log_exception("apply_worker")
            self.q.put(("error", str(e)))
        except Exception as e:
            log_exception("apply_worker")
            self.q.put(("error", "Injection failed: %s\n(Close the game if it is running and retry.)" % e))
        finally:
            self.busy = False

    def _refresh_buttons(self):
        """Only call this from the UI thread; it updates the apply buttons for the current state."""
        try:
            if hasattr(self, "apply_btn"):
                self.apply_btn.config(state=tk.NORMAL if (self.selected and self.photo_path) else tk.DISABLED)
        except Exception:
            pass
        try:
            if hasattr(self, "zip_btn"):
                self.zip_btn.config(state=tk.NORMAL if self.zip_matches else tk.DISABLED)
        except Exception:
            pass

    def restore_backup(self):
        assets = self.assets_path
        backup = os.path.join(os.path.dirname(assets), ASSETS_NAME + ".bak")
        if not os.path.isfile(backup):
            messagebox.showinfo("No Backup", "Backup file not found:\n%s" % backup)
            return
        if not messagebox.askyesno("Restore", "Restore the original game file from the backup?\n\n%s" % backup):
            return
        try:
            _atomic_replace(backup, assets)
            log_mod("restore", os.path.basename(backup), 1)
            messagebox.showinfo("Done", "Original file restored. Reloading characters\u2026")
            self.images = {}
            self.textures = []
            self.cards = {}
            self.selected = None
            threading.Thread(target=self.load_worker, args=(assets,), daemon=True).start()
            self.root.after(300, self.refresh_backup_list)
            self.root.after(300, self.refresh_status_page)
            self.root.after(300, self.refresh_home)
        except Exception as e:
            messagebox.showerror("Error", "Restore failed: %s\n(Close the game if it is running and retry.)" % e)

    # ---------------- ZIP page ----------------
    def create_zip_page(self, parent):
        page = self._fresh_page(parent)
        f, ic = self._page_shell(page, "Photo Pack (ZIP)",
                                     "Pick a ZIP with ready-made images. File names must match character names, e.g. fake_neighbour1.png.")
        self.zip_content = tk.Frame(ic, bg=PALETTE["bg.surface"])
        self.zip_content.pack(fill=tk.BOTH, expand=True)
        row = ttk.Frame(self.zip_content, style="Kart.TFrame")
        row.pack(fill=tk.X, pady=(0, 8))
        self.zip_path_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.zip_path_var, state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        ttk.Button(row, text=t("zip.choose_zip"), style="Secondary.TButton", command=self.pick_zip).pack(side=tk.LEFT)

        zip_list_frame = tk.Frame(self.zip_content, bg=PALETTE["bg.elevated"], highlightbackground=PALETTE["border.subtle"], highlightthickness=1)
        zip_list_frame.pack(fill=tk.BOTH, expand=True)
        self.zip_list = tk.Listbox(zip_list_frame, bg=PALETTE["bg.elevated"], fg=PALETTE["text.primary"], selectmode=tk.EXTENDED,
                                     relief=tk.FLAT, font=(FONT, 9))
        zip_scroll = ttk.Scrollbar(zip_list_frame, orient=tk.VERTICAL, command=self.zip_list.yview)
        self.zip_list.configure(yscrollcommand=zip_scroll.set)
        zip_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.zip_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6, pady=6)

        # ZIP loading indicator
        self.zip_loading = ttk.Progressbar(self.zip_content, mode="indeterminate", length=300)
        self.zip_loading_label = tk.Label(self.zip_content, text="", bg=PALETTE["bg.surface"], fg=PALETTE["accent.primary"], font=(FONT, 9))
        self.zip_loading.pack_forget()
        self.zip_loading_label.pack_forget()

        # Info panel
        info_frame = tk.Frame(self.zip_content, bg=PALETTE["bg.overlay"], highlightbackground=PALETTE["accent.primary"], highlightthickness=1)
        info_frame.pack(fill=tk.X, pady=(8, 4), padx=4)
        info_title = tk.Label(info_frame, text=t("zip.howto_title"),
                              bg=PALETTE["bg.overlay"], fg=PALETTE["accent.primary"], font=(FONT, 9, "bold"), anchor=tk.W)
        info_title.pack(fill=tk.X, padx=10, pady=(6, 2))
        info_text = (
            "1. De\u011fi\u015ftirmek istedi\u011finiz karakterlerin PNG/JPG g\u00f6rsellerini bir klas\u00f6re koyun.\n"
            "2. G\u00f6rsel isimlerinin karakter/texture adlar\u0131yla e\u015fle\u015fti\u011finden emin olun (Örn: fake_neighbour1.png).\n"
            "3. Klas\u00f6r\u00fc ZIP format\u0131nda s\u0131k\u0131\u015ft\u0131r\u0131n ve bu sayfaya s\u00fcr\u00fckleyin veya 'Import ZIP' butonunu kullan\u0131n.\n"
            "4. \u00d6nizlemeyi kontrol edip 'Apply ZIP to Game' butonuna bas\u0131n."
        )
        info_label = tk.Label(info_frame, text=info_text, bg=PALETTE["bg.overlay"], fg=PALETTE["text.muted"],
                              font=(FONT, 8), anchor=tk.W, justify=tk.LEFT, wraplength=600)
        info_label.pack(fill=tk.X, padx=10, pady=(0, 6))

        self.zip_status = ttk.Label(self.zip_content, text=t("zip.no_loaded"), style="Altbaslik.TLabel")
        self.zip_status.pack(anchor=tk.W, pady=(8, 4))
        self.zip_btn = ttk.Button(self.zip_content, text=t("zip.apply_to_game"), style="Primary.TButton", command=self.zip_apply,
                                   state=tk.DISABLED)
        self.zip_btn.pack(fill=tk.X, ipady=2)
        self.zip_empty = _build_empty_state(
            ic, "zip.empty.title", "zip.empty.body", "zip.empty.action",
            self.pick_zip, icon="\U0001F4E6")
        self._sync_zip_empty_state()
        return page

    def _sync_zip_empty_state(self) -> None:
        """Show the empty-state frame until a ZIP is chosen; then show the
        populated ZIP content."""
        if not hasattr(self, "zip_empty"):
            return
        if self.zip_file:
            self.zip_empty.pack_forget()
            self.zip_content.pack(fill=tk.BOTH, expand=True)
        else:
            self.zip_content.pack_forget()
            self.zip_empty.pack(fill=tk.BOTH, expand=True)

    def pick_zip(self):
        if self.busy:
            messagebox.showinfo("Busy", "An operation is already running. Please wait.")
            return
        y = filedialog.askopenfilename(title="Pick a ZIP of character images",
                                       initialdir=self.photo_dir,
                                       filetypes=[("ZIP", "*.zip"), ("All files", "*.*")])
        if not y:
            return
        self.zip_file = y
        self.photo_dir = os.path.dirname(y)
        self.save_pref("photo_dir", self.photo_dir)
        self.zip_loading_label.config(text=t("zip.scanning"))
        self.zip_loading.pack(pady=(4, 0))
        self.zip_loading_label.pack()
        self.zip_loading.start(30)
        self.root.update_idletasks()
        try:
            z = _open_zip(y)
        except PhotoPackError as e:
            self.zip_loading.stop()
            self.zip_loading.pack_forget()
            self.zip_loading_label.pack_forget()
            messagebox.showerror("Error", str(e))
            self.zip_file = None
            self.zip_matches = []
            self.zip_skipped = []
            return
        try:
            by_name = {name.lower(): name for name, w, h, fmt in self.textures}
            r = _scan_zip_for_characters(z, by_name, root=OUT_DIR)
            self.zip_matches = r["matches"]
            self.zip_skipped = r["skipped"]
            self.zip_unsafe = r["unsafe"]
            self.zip_too_large = r["too_large"]
            self.zip_dupes = r["dupes"]
        except PhotoPackError as e:
            self.zip_loading.stop()
            self.zip_loading.pack_forget()
            self.zip_loading_label.pack_forget()
            messagebox.showerror("Error", str(e))
            self.zip_file = None
            self.zip_matches = []
            self.zip_skipped = []
            return
        finally:
            z.close()
        self.zip_loading.stop()
        self.zip_loading.pack_forget()
        self.zip_loading_label.pack_forget()
        self.refresh_zip_info()
        self._sync_zip_empty_state()

    def refresh_zip_info(self):
        if not hasattr(self, "zip_list") or not self.zip_list.winfo_exists():
            return
        self.zip_list.delete(0, tk.END)
        for name, g in self.zip_matches:
            self.zip_list.insert(tk.END, "  \u2713  %s   <=  %s" % (name, os.path.basename(g)))
        for g in self.zip_skipped:
            self.zip_list.insert(tk.END, "  \u2717  %s   (no matching character)" % os.path.basename(g))
        for g in getattr(self, "zip_dupes", []):
            self.zip_list.insert(tk.END, "  \u26a0  %s   (duplicate \u2014 last one wins)" % os.path.basename(g))
        for g in getattr(self, "zip_too_large", []):
            self.zip_list.insert(tk.END, "  \u26a0  %s   (too large for one texture, skipped)" % os.path.basename(g))
        for g in getattr(self, "zip_unsafe", []):
            self.zip_list.insert(tk.END, "  \u2718  %s   (unsafe path, blocked)" % g)
        total = (len(self.zip_matches) + len(self.zip_skipped) + len(getattr(self, "zip_dupes", []))
                 + len(getattr(self, "zip_unsafe", [])) + len(getattr(self, "zip_too_large", [])))
        text = "%d matched, %d unmatched" % (len(self.zip_matches), len(self.zip_skipped))
        if getattr(self, "zip_dupes", []):
            text += ", %d duplicate name(s)" % len(self.zip_dupes)
        blocked = len(getattr(self, "zip_unsafe", [])) + len(getattr(self, "zip_too_large", []))
        if blocked:
            text += ", %d blocked" % blocked
        self.zip_status.config(text=t("zip.images_of_total") % (text, total))
        label_text = "Apply the ZIP now"
        if not self.zip_matches:
            label_text = "No ZIP loaded"
        self.zip_btn.config(state=tk.NORMAL if self.zip_matches else tk.DISABLED, text=label_text)

    def zip_apply(self):
        if not self.zip_matches or not self.zip_file:
            return
        if self.busy:
            messagebox.showinfo("Busy", "An operation is already running. Please wait.")
            return
        if not messagebox.askyesno("Apply ZIP", "%d character image(s) will be written into the game file."
                                   "\n\n%s" % (len(self.zip_matches), self.zip_file)):
            return
        self.zip_btn.config(state=tk.DISABLED)
        self.busy = True
        self.status_bar.start(40)
        threading.Thread(target=self.zip_worker, daemon=True).start()

    def zip_worker(self):
        self.busy = True
        try:
            assets = self.assets_path
            self.q.put(("status", "Reading the ZIP \u2026"))
            n = apply_zip_to_file(assets, self.zip_file, self.zip_matches,
                                  status=lambda t: self.q.put(("status", t)))
            log_mod("zip", os.path.basename(self.zip_file), n)
            self.q.put(("done", "%d character image(s) applied to the game.\n(A backup was made automatically.)" % n))
        except PhotoPackError as e:
            log_exception("zip_worker")
            self.q.put(("error", str(e)))
        except Exception as e:
            log_exception("zip_worker")
            self.q.put(("error", "ZIP apply failed: %s\n(Close the game if it is running and retry.)" % e))
        finally:
            self.busy = False

    # ---------------- mod manager page ----------------
    def create_manager(self, parent):
        page = self._fresh_page(parent)
        f, ic = self._page_shell(page, t("manager.title"))

        self.manager_content = tk.Frame(ic, bg=PALETTE["bg.surface"])
        self.manager_content.pack(fill=tk.BOTH, expand=True)

        # ============================================================
        # ÜST BÖLÜM — Yedek Al Butonu + Açıklama
        # ============================================================
        top_card = ttkb.Frame(self.manager_content, style="HomeCard.TFrame", padding=16)
        top_card.pack(fill=tk.X, pady=(0, 12))
        top_card.grid_columnconfigure(1, weight=1)

        ttkb.Button(top_card, text="\U0001F4BE  " + t("manager.backup_now"),  # 💾
                    style="ActionPrimary.TButton",
                    command=self.backup_now).grid(row=0, column=0, rowspan=1, sticky="nw", padx=(0, 12), pady=(0, 4))

        ttkb.Label(top_card, text=t("manager.backup_now_desc"),
                   font=("Segoe UI", 9),
                   foreground=PALETTE["text.secondary"],
                   background=PALETTE["bg.surface"],
                   wraplength=600, justify=tk.LEFT).grid(row=0, column=1, sticky="w")

        # ============================================================
        # YEDEK LİSTESİ PANELİ
        # ============================================================
        list_card = ttkb.Frame(self.manager_content, style="HomeCard.TFrame", padding=20)
        list_card.pack(fill=tk.BOTH, expand=True, pady=(0, 12))
        list_card.grid_columnconfigure(0, weight=1)
        list_card.grid_rowconfigure(1, weight=1)

        # Başlık satırı
        header_row = ttkb.Frame(list_card, style="HomeCardInner.TFrame")
        header_row.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        header_row.grid_columnconfigure(0, weight=1)

        ttkb.Label(header_row, text=t("manager.backups"),
                   font=("Segoe UI", 11, "bold"),
                   foreground=PALETTE["text.primary"],
                   background=PALETTE["bg.surface"]).grid(row=0, column=0, sticky="w")

        ttkb.Button(header_row, text="\u21BB  " + t("manager.refresh"),  # ↻
                    style="ActionSecondary.TButton",
                    command=self.refresh_backup_list).grid(row=0, column=1, sticky="e")

        # Listbox
        listbox_frame = ttkb.Frame(list_card, style="HomeCardInner.TFrame")
        listbox_frame.grid(row=1, column=0, sticky="nsew")
        listbox_frame.grid_columnconfigure(0, weight=1)
        listbox_frame.grid_rowconfigure(0, weight=1)

        self.backup_list = tk.Listbox(listbox_frame,
                                      bg=PALETTE["bg.surface"],
                                      fg=PALETTE["text.primary"],
                                      selectbackground=PALETTE["accent.primary"],
                                      selectforeground=PALETTE["text.primary"],
                                      relief=tk.FLAT,
                                      font=("Segoe UI", 10),
                                      borderwidth=0,
                                      highlightthickness=0,
                                      activestyle="none")
        self.backup_list.grid(row=0, column=0, sticky="nsew")

        bs = ttkb.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.backup_list.yview)
        bs.grid(row=0, column=1, sticky="ns")
        self.backup_list.configure(yscrollcommand=bs.set)

        # ============================================================
        # YEDEK AKSİYON BUTONLARI (yan yana, ikonlu)
        # ============================================================
        btn_row = ttkb.Frame(list_card, style="HomeCardInner.TFrame")
        btn_row.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        btn_row.grid_columnconfigure(0, weight=1)
        btn_row.grid_columnconfigure(1, weight=1)
        btn_row.grid_columnconfigure(2, weight=1)
        btn_row.grid_columnconfigure(3, weight=1)

        ttkb.Button(btn_row, text="\u21BA  " + t("manager.restore"),  # ↺
                    style="ActionPrimary.TButton",
                    command=self.restore_selected_backup).grid(row=0, column=0, sticky="ew", padx=(0, 6), ipady=6)
        ttkb.Button(btn_row, text="\U0001F4CB  " + t("manager.copy_to_data"),  # 📋
                    style="ActionSecondary.TButton",
                    command=self.copy_backup_to_data).grid(row=0, column=1, sticky="ew", padx=6, ipady=6)
        ttkb.Button(btn_row, text="\U0001F5D1  " + t("manager.delete"),  # 🗑
                    style="danger.TButton",
                    command=self.delete_backup).grid(row=0, column=2, sticky="ew", padx=6, ipady=6)
        ttkb.Button(btn_row, text="\U0001F4C1  " + t("manager.open_folder"),  # 📁
                    style="ActionSecondary.TButton",
                    command=lambda: self.open_path(BACKUP_DIR)).grid(row=0, column=3, sticky="ew", padx=(6, 0), ipady=6)

        # ============================================================
        # CACHE SATIRI
        # ============================================================
        cache_card = ttkb.Frame(self.manager_content, style="HomeCard.TFrame", padding=16)
        cache_card.pack(fill=tk.X)
        cache_card.grid_columnconfigure(1, weight=1)

        ttkb.Label(cache_card, text=t("manager.cache_label"),
                   font=("Segoe UI", 9),
                   foreground=PALETTE["text.secondary"],
                   background=PALETTE["bg.surface"]).grid(row=0, column=0, sticky="w")

        self.cache_lbl = ttkb.Label(cache_card, text="",
                                    font=("Segoe UI", 9),
                                    foreground=PALETTE["text.muted"],
                                    background=PALETTE["bg.surface"])
        self.cache_lbl.grid(row=0, column=1, sticky="w", padx=(8, 16))

        ttkb.Button(cache_card, text="\U0001F5D1  " + t("manager.clear_cache"),  # 🗑
                    style="danger.TButton",
                    command=self.clear_cache).grid(row=0, column=2, sticky="e", ipady=6, padx=(0, 4))
        ttkb.Button(cache_card, text="\U0001F4C1  " + t("manager.open_data"),  # 📁
                    style="ActionSecondary.TButton",
                    command=lambda: self.open_path(DATA_DIR)).grid(row=0, column=3, sticky="e", ipady=6)

        # Boş durum
        self.manager_empty = _build_empty_state(ic, "manager.empty.title",
                                                "manager.empty.body", "manager.empty.action", self.backup_now, icon="\U0001F4BE")
        self._sync_manager_empty_state()
        return page

    def _sync_manager_empty_state(self) -> None:
        """Show the empty-state frame when there are no backups yet; then
        show the populated manager content."""
        if not hasattr(self, "manager_empty"):
            return
        if getattr(self, "_backups", None):
            self.manager_empty.pack_forget()
            self.manager_content.pack(fill=tk.BOTH, expand=True)
        else:
            self.manager_content.pack_forget()
            self.manager_empty.pack(fill=tk.BOTH, expand=True)

    def backup_now(self):
        if not self.assets_path or not os.path.isfile(self.assets_path):
            messagebox.showwarning("Game file", "Game file not found.\nSet it first in Settings > Browse, or run Scan again.")
            return
        try:
            ensure_data_dirs()
            stamp = time_str().replace("-", "").replace(" ", "_").replace(":", "")
            dest = os.path.join(BACKUP_DIR, "%s_%s.bak" % (ASSETS_NAME, stamp))
            if os.path.exists(dest):
                dest = os.path.join(BACKUP_DIR, "%s_%s_1.bak" % (ASSETS_NAME, stamp))
            shutil.copy2(self.assets_path, dest)
            os.utime(dest, None)  # set mtime to current time
            log_mod("backup", os.path.basename(dest), 1)
            self.refresh_backup_list()
            self.root.after(200, self.refresh_status_page)
            messagebox.showinfo("Backup",
                                "%d MB copied to:\n\n%s" % (os.path.getsize(dest) // (1024 * 1024), dest))
        except Exception as e:
            messagebox.showerror("Error", "Backup failed: %s\n(Close the game if it is running and retry.)" % e)

    def gather_backups(self):
        files = []
        folder = os.path.dirname(self.assets_path) if self.assets_path else None
        if folder and os.path.isdir(folder):
            for fn in os.listdir(folder):
                p = os.path.join(folder, fn)
                if os.path.isfile(p) and (fn == ASSETS_NAME + ".bak" or fn == ASSETS_NAME + ".bak-yedek"
                                      or fn.endswith(".bak")):
                    files.append(p)
        if os.path.isdir(BACKUP_DIR):
            for fn in os.listdir(BACKUP_DIR):
                p = os.path.join(BACKUP_DIR, fn)
                if os.path.isfile(p):
                    files.append(p)
        seen = set()
        out = []
        for p in files:
            norm = os.path.normcase(os.path.normpath(p))
            if norm in seen:
                continue
            seen.add(norm)
            out.append(p)
        return sorted(out, key=lambda p: os.path.getmtime(p), reverse=True)

    def refresh_backup_list(self):
        if not hasattr(self, "backup_list") or not self.backup_list.winfo_exists():
            return
        self.backup_list.delete(0, tk.END)
        self._backups = []
        for p in self.gather_backups():
            sz = os.path.getsize(p) // (1024 * 1024)
            self._backups.append(p)
            self.backup_list.insert(tk.END, "  %s   (%d MB, %s)" % (os.path.basename(p), sz, file_mtime_str(p)))
        self._sync_manager_empty_state()
        self.cache_lbl.config(text=self.cache_size())

    def cache_size(self):
        try:
            total = 0
            for fn in os.listdir(CACHE_ROOT):
                p = os.path.join(CACHE_ROOT, fn)
                if os.path.isdir(p):
                    for root, _, names in os.walk(p):
                        for n in names:
                            try:
                                total += os.path.getsize(os.path.join(root, n))
                            except Exception:
                                pass
            return "(%d MB)" % (total // (1024 * 1024))
        except Exception:
            return ""

    def _selected_backup(self):
        idx = self.backup_list.curselection()
        if not idx or not getattr(self, "_backups", None):
            return None
        i = idx[0]
        if 0 <= i < len(self._backups):
            return self._backups[i]
        return None

    def restore_selected_backup(self):
        sel = self._selected_backup()
        if not sel:
            messagebox.showinfo("Select", "Pick a backup from the list first.")
            return
        if not self.assets_path or not os.path.isfile(self.assets_path):
            messagebox.showwarning("Game file", "Pick the game file first (Settings > Browse).")
            return
        if not messagebox.askyesno("Restore", "Replace the game file with this backup?\n\n%s" % sel):
            return
        try:
            _atomic_replace(sel, self.assets_path)
            log_mod("restore", os.path.basename(sel), 1)
            self.loader_lbl.config(text=t("status.restored") % os.path.basename(sel))
            messagebox.showinfo("Done", "Game file restored. Reloading characters\u2026")
            self.images = {}
            self.textures = []
            self.cards = {}
            self.selected = None
            threading.Thread(target=self.load_worker, args=(self.assets_path,), daemon=True).start()
            self.root.after(300, self.refresh_backup_list)
            self.root.after(300, self.refresh_status_page)
            self.root.after(300, self.refresh_home)
        except Exception as e:
            messagebox.showerror("Error", "Restore failed: %s\n(Close the game if it is running and retry.)" % e)

    def copy_backup_to_data(self):
        sel = self._selected_backup()
        if not sel:
            messagebox.showinfo("Select", "Pick a backup from the list first.")
            return
        try:
            ensure_data_dirs()
            dst = os.path.join(BACKUP_DIR, os.path.basename(sel))
            shutil.copy2(sel, dst)
            os.utime(dst, None)  # set mtime to current time
            self.refresh_backup_list()
            messagebox.showinfo("Done", "Copied to:\n%s" % dst)
        except Exception as e:
            messagebox.showerror("Error", "Copy failed: %s" % e)

    def delete_backup(self):
        sel = self._selected_backup()
        if not sel:
            messagebox.showinfo("Select", "Pick a backup from the list first.")
            return
        if not messagebox.askyesno("Delete", "Delete this backup permanently?\n\n%s" % sel):
            return
        try:
            os.remove(sel)
            self.refresh_backup_list()
            messagebox.showinfo("Done", "Backup deleted.")
        except Exception as e:
            messagebox.showerror("Error", "Delete failed: %s" % e)

    # ---------------- game status page ----------------
    def create_status(self, parent):
        page = self._fresh_page(parent)
        f, ic = self._page_shell(page, t("status.title"),
                                     "What the tool did, when, and whether the game file is currently modified.")

        self.status_content = tk.Frame(ic, bg=PALETTE["bg.surface"])
        self.status_content.pack(fill=tk.BOTH, expand=True)

        # ---- Status Text Paneli ----
        # tk.Text korundu (ttkbootstrap Text yok), sade dark modern stil
        # wrap=tk.NONE + yatay scrollbar: pencere sürükleme sırasında word-wrap
        # yeniden hesaplaması (re-wrap) engellenir → takılma gider.
        text_box = tk.Frame(self.status_content, bg=PALETTE["bg.surface"],
                            highlightbackground=PALETTE["border.subtle"], highlightthickness=1)
        text_box.pack(fill=tk.BOTH, expand=True, padx=0, pady=(0, 12))

        self.status_text = tk.Text(text_box, bg=PALETTE["bg.surface"], fg=PALETTE["text.primary"],
                                   relief=tk.FLAT, wrap=tk.NONE, font=("Segoe UI", 10),
                                   padx=20, pady=20, insertbackground=PALETTE["text.primary"])
        st = ttkb.Scrollbar(text_box, orient=tk.VERTICAL, command=self.status_text.yview)
        hsb = ttkb.Scrollbar(text_box, orient=tk.HORIZONTAL, command=self.status_text.xview)
        self.status_text.configure(yscrollcommand=st.set, xscrollcommand=hsb.set, state=tk.DISABLED)
        st.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # ---- Alt Buton Satırı (yan yana) ----
        btn_row = ttkb.Frame(self.status_content, style="HomeCardInner.TFrame")
        btn_row.pack(fill=tk.X, padx=12, pady=8)

        ttkb.Button(btn_row, text="\u2713  " + t("status.verify_file"),  # ✓
                    style="ActionPrimary.TButton",
                    command=self.verify_game_file).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 6), ipady=8)
        ttkb.Button(btn_row, text="\U0001F4C1  " + t("home.open_game_folder"),  # 📁
                    style="ActionSecondary.TButton",
                    command=lambda: self.open_path(os.path.dirname(self.assets_path) if self.assets_path else PROJECT_DIR)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=6, ipady=8)
        ttkb.Button(btn_row, text="\u21BB  " + t("common.refresh"),  # ↻
                    style="ActionSecondary.TButton",
                    command=self.refresh_status_page).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(6, 0), ipady=8)

        self.status_empty = _build_empty_state(ic, "status.empty.title",
                                               "status.empty.body",
                                               "status.empty.action", self.browse_assets, icon="\U0001F4CA")
        self._sync_status_empty_state()
        return page

    def _sync_status_empty_state(self) -> None:
        """Show the empty-state frame until a game file is set; then show
        the populated status content."""
        if not hasattr(self, "status_empty"):
            return
        game_ok = bool(self.assets_path and os.path.isfile(self.assets_path))
        if game_ok:
            self.status_empty.pack_forget()
            self.status_content.pack(fill=tk.BOTH, expand=True)
        else:
            self.status_content.pack_forget()
            self.status_empty.pack(fill=tk.BOTH, expand=True)

    def refresh_status_page(self):
        if not hasattr(self, "status_text") or not self.status_text.winfo_exists():
            return
        self._sync_status_empty_state()

        # ---- Cache kontrolü: veri kaynağı değişmediyse I/O ve widget güncelleme atla ----
        p = self.assets_path
        game_mtime = os.path.getmtime(p) if (p and os.path.isfile(p)) else 0
        hist_mtime = os.path.getmtime(HISTORY_FILE) if os.path.isfile(HISTORY_FILE) else 0
        backup_dir_mtime = os.path.getmtime(BACKUP_DIR) if os.path.isdir(BACKUP_DIR) else 0
        game_dir_mtime = os.path.getmtime(os.path.dirname(p)) if (p and os.path.isdir(os.path.dirname(p))) else 0

        cache_key = (game_mtime, hist_mtime, backup_dir_mtime, game_dir_mtime)
        if hasattr(self, "_status_cache_key") and self._status_cache_key == cache_key:
            return  # Hiçbir şey değişmedi, yenilemeye gerek yok

        # Cache miss: yeniden oluştur
        lines = []
        if p and os.path.isfile(p):
            lines.append("Game file")
            lines.append("    %s" % p)
            lines.append("    Size: %d MB   |   last modified: %s"
                         % (os.path.getsize(p) // (1024 * 1024), file_mtime_str(p)))
        else:
            lines.append("Game file: not set yet. Use Settings > Browse or Scan.")
        lines.append("")
        hist = mod_history()
        applied = hist.get("applied", [])
        lines.append("Mod history  (%d action%s)" % (len(applied), "" if len(applied) == 1 else "s"))
        for e in reversed(applied[-15:]):
            amount = ("%d item(s)  " % e["n"]) if e.get("n") else ""
            lines.append("    %s   %-8s  %s%s" % (e.get("ts", ""), e.get("kind", ""), amount, e.get("detail", "")))
        if not applied:
            lines.append("    Nothing applied yet: your game file is untouched.")
        lines.append("")
        backups = self.gather_backups()
        lines.append("Backups: %d found in the game folder / data\\backups" % len(backups))
        for b in backups[:6]:
            lines.append("    %s  (%d MB)" % (os.path.basename(b), os.path.getsize(b) // (1024 * 1024)))
        if len(backups) > 6:
            lines.append("    \u2026 and %d more" % (len(backups) - 6))

        text_content = "\n".join(lines)
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete("1.0", tk.END)
        self.status_text.insert("1.0", text_content)
        self.status_text.config(state=tk.DISABLED)

        # Cache'i güncelle
        self._status_cache_key = cache_key

    def verify_game_file(self):
        if not self.assets_path or not os.path.isfile(self.assets_path):
            messagebox.showwarning("Game file", "Game file not found.")
            return
        if self.busy:
            messagebox.showinfo("Busy", "An operation is already running. Please wait.")
            return
        self.busy = True
        self.status_bar.start(40)
        threading.Thread(target=self.verify_worker, daemon=True).start()

    def verify_worker(self):
        try:
            cur = file_md5(self.assets_path)
            ref = os.path.join(os.path.dirname(self.assets_path), ASSETS_NAME + ".bak-yedek")
            if not os.path.isfile(ref):
                ref = os.path.join(os.path.dirname(self.assets_path), ASSETS_NAME + ".bak")
            orig = None
            if os.path.isfile(ref):
                orig = file_md5(ref)
            self.q.put(("verify", cur, orig))
        except Exception as e:
            log_exception("verify_worker")
            self.q.put(("error", "Verify failed: %s" % e))
        finally:
            self.busy = False
    # ---------------- settings page ----------------
    def create_settings(self, parent):
        page = self._fresh_page(parent)
        f, ic = self._page_shell(page, t("settings.title"), "Game detection & file locations.")
        row = ttk.Frame(ic, style="Kart.TFrame")
        row.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(row, text=self.assets_path if self.assets_path else "Game data file (sharedassets0.assets)",
                  style="Soluk.TLabel").pack(side=tk.LEFT, anchor=tk.W)
        ttk.Button(row, text=t("settings.browse"), style="Primary.TButton", command=self.browse_assets).pack(side=tk.LEFT, padx=8)
        ttk.Button(row, text=t("settings.scan_again"), style="Secondary.TButton", command=lambda: self.auto_detect(force=True)).pack(side=tk.LEFT)

        lang_row = ttk.Frame(ic, style="Kart.TFrame")
        lang_row.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(lang_row, text=t("settings.language")+":", style="Soluk.TLabel").pack(side=tk.LEFT, anchor=tk.W)
        self.lang_var = tk.StringVar(value=get_current_language())
        lang_combo = ttk.Combobox(lang_row, textvariable=self.lang_var, values=["en", "tr"],
                                   state="readonly", width=8)
        lang_combo.pack(side=tk.LEFT, padx=8)
        _pending_lang_id = [None]
        def on_lang_change(event=None):
            if _pending_lang_id[0] is not None:
                self.root.after_cancel(_pending_lang_id[0])
            def _apply():
                _pending_lang_id[0] = None
                combo_widget = lang_combo
                _values = ["en", "tr"]
                _idx = -1
                try:
                    _idx = combo_widget.current()
                except Exception:
                    pass
                if _idx < 0 or _idx >= len(_values):
                    try:
                        _raw = combo_widget.get()
                        if _raw in _values:
                            _idx = _values.index(_raw)
                    except Exception:
                        pass
                if _idx < 0 or _idx >= len(_values):
                    return
                lang = _values[_idx]
                self.save_pref("language", lang)
                load_language(lang)
                messagebox.showinfo(t("settings.language"), t("settings.restart_hint"))
            _pending_lang_id[0] = self.root.after(300, _apply)
        lang_combo.bind("<<ComboboxSelected>>", on_lang_change)

        meta = tk.Frame(ic, bg=COLORS["panel"], highlightbackground=COLORS["border"], highlightthickness=1)
        meta.pack(fill=tk.BOTH, expand=True)
        self.settings_info = tk.Text(meta, bg=COLORS["panel"], fg=COLORS["muted"], relief=tk.FLAT, wrap=tk.WORD,
                                      font=(FONT, 9))
        self.settings_info.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        restore = ttk.Frame(ic, style="Kart.TFrame")
        restore.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(restore, text=t("settings.restore_original"), style="Danger.TButton",
                   command=self.restore_backup).pack(side=tk.LEFT)
        self.status_bar = ttk.Progressbar(ic, mode="indeterminate")
        self.status_bar.pack(fill=tk.X, pady=(10, 4))
        self.status_lbl = ttk.Label(ic, text="", style="Soluk.TLabel", anchor=tk.W)
        self.status_lbl.pack(fill=tk.X)
        return page

    def browse_assets(self):
        y = filedialog.askopenfilename(title="Select sharedassets0.assets",
                                       initialdir=os.path.dirname(self.assets_path) if self.assets_path else os.path.expanduser("~"),
                                       filetypes=[("Unity Assets", "*.assets"), ("All files", "*.*")])
        if y:
            self.set_game_file(y, [])

    def auto_detect(self, force=False):
        if self.assets_path and os.path.isfile(self.assets_path) and not force:
            return
        threading.Thread(target=self.scan_worker, daemon=True).start()

    def scan_worker(self):
        try:
            self.q.put(("status", "Scanning your computer for the game\u2026"))
            candidates = find_candidate_files()
            if not candidates:
                self.q.put(("target_missing",))
                return
            self.q.put(("found", candidates[0], candidates))
        except Exception as e:
            log_exception("scan_worker")
            self.q.put(("error", "Scan failed: %s" % e))

    def set_game_file(self, path, candidates):
        self.assets_path = path
        self.save_pref("assets", path)
        if hasattr(self, "settings_info"):
            info = ["Selected: %s" % path, ""]
            if candidates:
                info.append("Other candidates found:")
                for i, p in enumerate(candidates[1:10]):
                    info.append("  %d) %s" % (i + 1, p))
            if os.path.isfile(path):
                info.append("\nFile exists (%d MB)." % (os.path.getsize(path) // (1024 * 1024)))
            self.settings_info.delete("1.0", tk.END)
            self.settings_info.insert("1.0", "\n".join(info))
        self.refresh_home()
        if not self.textures:
            threading.Thread(target=self.load_worker, args=(path,), daemon=True).start()

    # ---------------- stack ----------------
    def drain_messages(self):
        try:
            while True:
                tip, *data = self.q.get_nowait()
                if tip == "results":
                    items, thumbs = data
                    self.textures = items
                    self.images = thumbs
                    self.visible_names = []
                    self.selected = None
                    self.build_cards()
                    self.refresh_gallery()
                    self.status_bar.stop()
                    self.status_lbl.config(text=t("status.characters_ready")
                                            % len(items), style="Bilgi.TLabel")
                elif tip == "status":
                    self.status_lbl.config(text=data[0], style="Altbaslik.TLabel")
                elif tip == "error":
                    self.status_bar.stop()
                    self.status_lbl.config(text=data[0], style="Tehlike.TLabel")
                    self._refresh_buttons()
                    messagebox.showerror("Error", data[0])
                elif tip == "done":
                    self.status_bar.stop()
                    self.status_lbl.config(text=data[0], style="Bilgi.TLabel")
                    self._refresh_buttons()
                    messagebox.showinfo("Success",
                                        data[0] + "\n\nRestart the game to see the change.\n"
                                                  "Use Mod Manager to restore a backup or verify the game file.")
                    self.root.after(200, self.refresh_backup_list)
                    self.root.after(200, self.refresh_status_page)
                elif tip == "found":
                    path, candidates = data
                    self.set_game_file(path, candidates)
                elif tip == "target_missing":
                    self.status_bar.stop()
                    self.status_lbl.config(text=t("status.game_not_found_hint"),
                                           style="Tehlike.TLabel")
                elif tip == "gallery_loading_start":
                    self.gallery_loading_label.config(text=data[0] if data else "Loading...")
                    self.gallery_loading.pack(pady=10)
                    self.gallery_loading_label.pack()
                    self.gallery_loading.start(30)
                elif tip == "gallery_loading_stop":
                    self.gallery_loading.stop()
                    self.gallery_loading.pack_forget()
                    self.gallery_loading_label.pack_forget()
                elif tip == "verify":
                    cur, orig = data
                    self.status_bar.stop()
                    if orig and cur == orig:
                        state = "\u2713 Game file matches the original backup (unmodified)"
                        style = "Bilgi.TLabel"
                    elif orig:
                        state = "\u2718 Game file differs from the original (modified)"
                        style = "Tehlike.TLabel"
                    else:
                        state = "\u26a0 Original backup not found \u2014 compare not possible"
                        style = "Altbaslik.TLabel"
                    messagebox.showinfo("Verify", "%s\n\nCurrent MD5:\n%s" % (state, cur))
                    self.status_lbl.config(text=state, style=style)
                    self.refresh_status_page()
        except queue.Empty:
            pass
        # Polling aralığı: 200ms (eski 100ms). Pencere sürükleme sırasında
        # event queue yükünü azaltır; UI tepki süresi 200ms hâlâ kabul edilebilir.
        self.root.after(200, self.drain_messages)


def _cli_out(message: str) -> None:
    """Write a CLI diagnostic line to stdout; no-op when stdout is missing
    (a frozen EXE built without a console) or the write fails."""
    try:
        if sys.stdout is not None:
            sys.stdout.write(message + "\n")
    except Exception:
        logging.getLogger(LOGGER_NAME).debug("stdout unavailable for CLI output")


def _run_lang_test(target_lang):
    root = tk.Tk()
    root.withdraw()
    app = App(root)
    def _test():
        try:
            app.lang_var.set(target_lang)
            app.save_pref("language", target_lang)
            with io.open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            _cli_out("LANG_TEST: saved=%r  file=%r" % (target_lang, saved.get("language")))
            _cli_out("LANG_TEST: %s" % ("PASS" if saved.get("language") == target_lang else "FAIL"))
        except Exception as e:
            _cli_out("LANG_TEST ERROR: %s" % e)
        root.destroy()
    root.after(500, _test)
    root.mainloop()


def _enable_dpi_awareness() -> None:
    """Enable per-monitor DPI awareness on Windows; no-op elsewhere.
    Must run before Tk() is created."""
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # type: ignore[attr-defined]
    except Exception as e:
        logger.debug("DPI awareness not enabled: %s", e)


def _apply_tk_scaling(root: tk.Tk) -> None:
    """Scale ttk text sizes from the system DPI (pixels-per-point = DPI / 72)."""
    try:
        import ctypes
        dpi = int(ctypes.windll.user32.GetDpiForSystem())  # type: ignore[attr-defined]
        scale = dpi / 72.0
        root.tk.call("tk", "scaling", scale)
    except Exception as e:
        logger.debug("tk scaling not adjusted: %s", e)


def main():
    _enable_dpi_awareness()
    install_global_exception_handlers()
    if "--selftest" in sys.argv:
        run_selftest()
        return
    if "--assettest" in sys.argv:
        run_assettest()
        return
    if "--test-lang-tr" in sys.argv:
        _run_lang_test("tr")
        return
    if "--test-lang-en" in sys.argv:
        _run_lang_test("en")
        return
    if not _acquire_single_instance():
        try:
            import tkinter.messagebox as _mb
            _mb.showerror("NH Mod Tool is already running", "An instance of NH Mod Tool is already open.")
        except Exception:
            pass
        return
    root = ttkb.Window(themename="darkly")
    app = App(root)                    # App class tanımlı olmalı, satır 643
    install_global_exception_handlers(app)
    root.mainloop()


_MUTEX_HANDLE = None


def _acquire_single_instance():
    global _MUTEX_HANDLE
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        name = "Global\\S1VRA_NHModTool_%s" % APP_VERSION.replace(".", "_")
        _MUTEX_HANDLE = kernel32.CreateMutexW(None, False, name)
        if ctypes.GetLastError() == 183:
            kernel32.CloseHandle(_MUTEX_HANDLE)
            _MUTEX_HANDLE = None
            return False
        return True
    except Exception:
        return True


def run_selftest():
    report = {"version": APP_VERSION, "tests": [], "ok": True}

    def ok(name, info=""):
        report["tests"].append({"name": name, "pass": True, "info": info})

    def fail(name, info=""):
        report["tests"].append({"name": name, "pass": False, "info": info})
        report["ok"] = False

    import tempfile
    base = tempfile.mkdtemp(prefix="nh_selftest_")
    dirs = ["data", "data/logs", "data/cache", "data/tmp", "data/backups"]
    for d in dirs:
        try:
            os.makedirs(os.path.join(base, d), exist_ok=True)
            ok("mkdir_%s" % d)
        except Exception as e:
            fail("mkdir_%s" % d, str(e))
    legacy = os.path.join(base, "nh_mod_tool_settings.json")
    try:
        with io.open(legacy, "w", encoding="utf-8") as f:
            json.dump({"assets": "X"}, f)
    except Exception:
        pass
    hist_path = os.path.join(base, "data", "mod_history.json")
    settings_path = os.path.join(base, "data", "settings.json")
    apply_patch = {"HISTORY_FILE": hist_path, "SETTINGS_FILE": settings_path, "DATA_DIR": os.path.join(base, "data")}
    old_hist = globals().get("HISTORY_FILE")
    old_set = globals().get("SETTINGS_FILE")
    try:
        globals()["HISTORY_FILE"] = hist_path
        globals()["SETTINGS_FILE"] = settings_path
        globals()["DATA_DIR"] = os.path.join(base, "data")
        log_mod("selftest", "test entry", 7)
        h = mod_history()
        if h["applied"] and h["applied"][0]["kind"] == "selftest":
            ok("history_append")
        else:
            fail("history_append")
        globals()["HISTORY_FILE"] = old_hist
        globals()["SETTINGS_FILE"] = old_set
    except Exception as e:
        fail("history_append", str(e))
        globals()["HISTORY_FILE"] = old_hist
        globals()["SETTINGS_FILE"] = old_set

    img = Image.new("RGBA", (128, 128), (255, 0, 0, 255))
    img2 = img.convert("RGB")
    ok("pillow_rgba_to_rgb", "%dx%d" % img2.size)

    cache_file = os.path.join(base, "data", "cache", "sample.png")
    try:
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        img.save(cache_file)
        loaded = Image.open(cache_file).convert("RGBA")
        ok("cache_persist")
    except Exception as e:
        fail("cache_persist", str(e))

    src = os.path.join(base, "test_src.bin")
    dst = os.path.join(base, "test_dst.bin")
    try:
        with io.open(src, "wb") as f:
            f.write(b"X" * 2048)
        _atomic_replace(src, dst)
        with io.open(dst, "rb") as f:
            assert f.read() == b"X" * 2048
        ok("atomic_replace")
    except Exception as e:
        fail("atomic_replace", str(e))

    try:
        out_path = os.path.join(base, "image_test_out.png")
        with Image.open(cache_file) as test_img:
            test_img.save(out_path)
        ok("image_save_load", "structure ok")
    except Exception as e:
        fail("image_save_load", str(e))

    try:
        # base is a tempfile.mkdtemp() directory this run created itself,
        # so it is its own managed root; the gate still applies so an
        # accidental substitution can never widen what gets removed.
        if is_under_managed_root(base, [Path(base)]):
            shutil.rmtree(base, ignore_errors=True)
    except Exception:
        pass

    out = sys.argv[sys.argv.index("--selftest") + 1] if "--selftest" in sys.argv and len(sys.argv) > sys.argv.index("--selftest") + 1 else ""
    if not out:
        out = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])) if sys.argv else ".", "selftest_report.json")
    try:
        with io.open(out, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
    except Exception:
        pass
    sys.exit(0 if report["ok"] else 1)


def _write_json(path, payload):
    with io.open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def run_assettest():
    """Headless diagnostics for the in-game texture pipeline.

    Reproduces the exact load_worker code path (UnityPy.load, Texture2D scan,
    obj.read().image, RGBA/thumbnail conversion, PNG cache write) so a frozen
    build that fails silently in the GUI reports its real exception here.

    Invoked by:  NHModTool.exe --assettest <outdir>
    Writes:      <outdir>/assettest_report.json   (exit 0 = all decodable)
    """
    report = {"version": APP_VERSION,
              "frozen": bool(getattr(sys, "frozen", False)),
              "pass": True, "tests": [], "errors": [], "paths": {}}

    def ok(name, info=""):
        report["tests"].append({"name": name, "pass": True, "info": info})

    def fail(name, info=""):
        report["tests"].append({"name": name, "pass": False, "info": info})
        report["pass"] = False

    idx = sys.argv.index("--assettest")
    outdir = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "."
    try:
        os.makedirs(outdir, exist_ok=True)
    except Exception:
        outdir = "."

    report["paths"] = {
        "project_dir": PROJECT_DIR,
        "bundle_dir": BUNDLE_DIR,
        "data_dir": DATA_DIR,
        "cache_root": CACHE_ROOT,
        "settings_file": SETTINGS_FILE,
    }

    assets = ""
    try:
        with io.open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            st = json.load(f)
        assets = (st or {}).get("assets") or ""
    except Exception as e:
        report["errors"].append({"stage": "read_settings", "error": repr(e)})
    if not assets or not os.path.isfile(assets):
        try:
            cands = find_candidate_files()
            if cands:
                assets = cands[0]
        except Exception as e:
            report["errors"].append({"stage": "auto_detect", "error": repr(e)})
    if not assets or not os.path.isfile(assets):
        fail("assets_found", "no game file (settings assets missing / not on disk)")
        out_full = {"version": APP_VERSION, "pass": report["pass"],
                    "tests": report["tests"], "errors": report["errors"], "paths": report["paths"]}
        try:
            _write_json(os.path.join(outdir, "assettest_report.json"), out_full)
        except Exception:
            pass
        sys.exit(1)
    report["paths"]["assets"] = assets
    ok("assets_found", assets)

    import tempfile
    tmp = tempfile.mkdtemp(prefix="nh_assettest_")
    try:
        try:
            env = UnityPy.load(assets)
            ok("unitypy_load", getattr(UnityPy, "__version__", "n/a"))
        except Exception as e:
            fail("unitypy_load", "%s: %s" % (type(e).__name__, e))
            out_full = {"version": APP_VERSION, "pass": report["pass"],
                        "tests": report["tests"], "errors": report["errors"], "paths": report["paths"]}
            _write_json(os.path.join(outdir, "assettest_report.json"), out_full)
            sys.exit(1)

        total_tex = 0
        items = []
        by_name = {}
        read_fails = []
        for obj in env.objects:
            if obj.type.name != "Texture2D":
                continue
            total_tex += 1
            try:
                d = obj.read()
            except Exception as e:
                read_fails.append((getattr(obj, "path_id", "?"), "%s: %s" % (type(e).__name__, e)))
                continue
            name = d.m_Name or ""
            lower = name.lower()
            if not lower.startswith("fake_") or "photo" in lower:
                continue
            items.append((name, d.m_Width, d.m_Height, d.m_TextureFormat))
            by_name[name] = obj
        items.sort(key=lambda x: x[0].lower())
        ok("scan", "Texture2D total=%d, fake_*=%d" % (total_tex, len(items)))
        if read_fails:
            report["errors"].append({"stage": "obj_read", "count": len(read_fails),
                                     "sample": read_fails[:10]})

        decodes_ok = 0
        decode_fails = []
        sample = items[:40]
        for name, w, h, fmt in sample:
            try:
                img = make_thumb_impl(by_name[name].read().image)
                tp = os.path.join(tmp, safe_name(name) + ".png")
                img.save(tp)
                decodes_ok += 1
            except Exception as e:
                decode_fails.append({"name": name, "format": fmt,
                                     "error": "%s: %s" % (type(e).__name__, e),
                                     "trace": "fallback"} )
        if decode_fails:
            report["errors"].append({"stage": "thumbnail_decode", "ok": decodes_ok,
                                     "failed": len(decode_fails), "sample": decode_fails[:10]})
        if items:
            if decodes_ok and decodes_ok == len(sample):
                ok("decode", "%d/%d sample textures -> RGBA thumbnails" % (decodes_ok, len(sample)))
            else:
                fail("decode", "%d/%d sample textures decoded" % (decodes_ok, len(sample)))
        else:
            fail("decode", "no fake_* textures found")

        cache_probe = os.path.join(CACHE_ROOT, "assettest_probe")
        try:
            os.makedirs(CACHE_ROOT, exist_ok=True)
            with io.open(cache_probe, "w", encoding="utf-8") as f:
                f.write("1")
            os.remove(cache_probe)
            ok("cache_writable", CACHE_ROOT)
        except Exception as e:
            fail("cache_writable", repr(e))
    finally:
        try:
            # tmp is tempfile.mkdtemp() output owned by this run, so it is
            # its own managed root; the safety gate still applies.
            if is_under_managed_root(tmp, [Path(tmp)]):
                shutil.rmtree(tmp, ignore_errors=True)
        except Exception:
            pass
    out_full = {"version": APP_VERSION, "pass": report["pass"],
                "tests": report["tests"], "errors": report["errors"], "paths": report["paths"]}
    try:
        _write_json(os.path.join(outdir, "assettest_report.json"), out_full)
    except Exception:
        pass
    sys.exit(0 if report["pass"] else 1)


def make_thumb_impl(img):
    g = img.convert("RGBA")
    g.thumbnail((THUMB_W, THUMB_H), Image.LANCZOS)
    return g


if __name__ == "__main__":
    main()