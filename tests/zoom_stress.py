# -*- coding: utf-8 -*-
"""Zoom stress driver. Runs the real App against a COPY-free read of the game
assets (load_worker only reads), then hammers zoom_step/zoom_reset in the main
thread while pumping the Tk event loop -- the way a user zooms rapidly.

If the app dies silently (the reported bug), faulthandler dumps the stack so we
can see exactly where it happens. The script prints progress and exits 0 only
if no crash and no exception occurred.
"""
import os
import sys
import json
import time
import tempfile
import faulthandler
import signal as _signal
import tkinter as tk

faulthandler.enable()
for _sig in (getattr(_signal, "SIGSEGV", None), getattr(_signal, "SIGABRT", None),
             getattr(_signal, "SIGFPE", None), getattr(_signal, "SIGILL", None)):
    if _sig is not None:
        try:
            faulthandler.register(_sig)
        except Exception:
            pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

REAL_ASSETS = r"C:\Users\mehmet\AppData\Games\No, I'm not a Human\NoImNotAHuman_Data\sharedassets0.assets"

import NHModTool as appmod  # noqa: E402

tmp = tempfile.mkdtemp(prefix="nh_zoom_stress_")
appmod.DATA_DIR = os.path.join(tmp, "data")
appmod.CACHE_ROOT = os.path.join(appmod.DATA_DIR, "cache")
appmod.TMP_DIR = os.path.join(appmod.DATA_DIR, "tmp")
appmod.BACKUP_DIR = os.path.join(appmod.DATA_DIR, "backups")
appmod.OUT_DIR = appmod.TMP_DIR
appmod.LOG_DIR = os.path.join(appmod.DATA_DIR, "logs")
appmod.HISTORY_FILE = os.path.join(appmod.DATA_DIR, "mod_history.json")
appmod.SETTINGS_FILE = os.path.join(appmod.DATA_DIR, "settings.json")

os.makedirs(appmod.DATA_DIR, exist_ok=True)
if os.path.isfile(REAL_ASSETS):
    with open(appmod.SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump({"assets": REAL_ASSETS, "zoom": 1.0}, f)
    print("assets: %s (%d MB)" % (REAL_ASSETS, os.path.getsize(REAL_ASSETS) // (1024 * 1024)))
else:
    print("WARN: real asset file missing; textures will be empty")

sys.stdout.flush()
print("instantiating App...")
sys.stdout.flush()
root = tk.Tk()
app = appmod.App(root)

deadline = time.time() + 60
while time.time() < deadline and not app.textures and not app.busy:
    root.update()
    time.sleep(0.02)
print("loaded textures:", len(app.textures))
sys.stdout.flush()

if not app.textures:
    print("NO_TEXTURES_ABORT")
    try:
        root.destroy()
    except Exception:
        pass
    sys.exit(2)

app.show_page("photos")
t0 = time.time()
try:
    iterations = 2000
    for i in range(iterations):
        if i % 3 == 2:
            app.zoom_reset()
        else:
            app.zoom_step(1 if i % 2 == 0 else -1)
        if i % 40 == 0:
            app.canvas.yview_scroll(25, "units")
            app._repair_visible_cells()
            app.canvas.yview_scroll(-25, "units")
            app._repair_visible_cells()
        root.update()
        if i % 250 == 0:
            print("  iter %d/%d  zoom=%.2f  cards=%d  dirty=%d"
                  % (i, iterations, app.zoom, len(app.cards),
                     sum(1 for c in app.cards.values() if c.get("img_dirty"))))
            sys.stdout.flush()
except Exception as e:
    import traceback
    traceback.print_exc()
    print("STRESS_RAISED: %r" % (e,))
    try:
        root.destroy()
    except Exception:
        pass
    sys.exit(3)

elapsed = time.time() - t0
print("STRESS_DONE_OK iterations=%d elapsed=%.1fs textures=%d cards=%d zoom=%.2f"
      % (iterations, elapsed, len(app.textures), len(app.cards), app.zoom))
root.update()
try:
    from PIL import ImageGrab
    bbox = (root.winfo_rootx(), root.winfo_rooty(),
            root.winfo_rootx() + root.winfo_width(), root.winfo_rooty() + root.winfo_height())
    shot = ImageGrab.grab(bbox)
    out = os.path.join(ROOT, "tests", "outputs", "zoom_fix.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    shot.save(out)
    print("screenshot: %s (%dx%d)" % (out, shot.size[0], shot.size[1]))
except Exception as e:
    print("screenshot failed: %r" % (e,))
try:
    root.destroy()
except Exception:
    pass
sys.exit(0)