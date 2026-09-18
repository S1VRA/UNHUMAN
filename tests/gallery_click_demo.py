# -*- coding: utf-8 -*-
"""Real-window demo of the fixed gallery click: scroll -> click -> correct card.

Two canvases side by side:
  - ONCE : buggy handler  (raw evt.x/evt.y passed to find_overlapping)
  - SONRA: fixed handler  (canvasx/canvasy conversion)
Both canvases are scrolled identically and a real <Button-1> event is generated
at the same widget position on each. A screenshot is saved for the user.
"""
import os
import sys
import tkinter as tk
from PIL import ImageGrab

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "tests", "outputs", "character_match_fix.png")

N = 12
GAP = 12
CELL = 100
PITCH = 112
CV_W = 260
CV_H = 260
FILLS = ["#7bb8e6", "#e6a87b", "#8fe68f", "#c98fe6"]


def build_gallery(container, fixed):
    box = tk.Frame(container, bd=1, relief=tk.SUNKEN)
    head = tk.Label(box, text=("SONRA  (canvasx/canvasy ile)" if fixed else "ONCE  (ham evt koordinatiyla)"),
                    font=("TkDefaultFont", 10, "bold"))
    head.pack(side=tk.TOP, fill=tk.X)
    cv = tk.Canvas(box, width=CV_W, height=CV_H, bg="white", highlightthickness=0)
    cv.pack()
    cap = tk.Label(box, text="Henuz secilmedi", font=("TkDefaultFont", 9), fg="black")
    cap.pack(side=tk.BOTTOM, fill=tk.X)
    items = {}

    def click(evt):
        if fixed:
            x, y = cv.canvasx(evt.x), cv.canvasy(evt.y)
        else:
            x, y = evt.x, evt.y
        name = None
        for iid in reversed(cv.find_overlapping(x, y, x, y)):
            if iid in items:
                name = items[iid]
                break
        if name is None:
            cap.config(text="Secilen: HIC (bos)", fg="black")
        elif name == "card05":
            cap.config(text="Secilen: %s  -> DOGRU kart" % name, fg="green")
        else:
            cap.config(text="Secilen: %s  -> YANLIS kart (bug)" % name, fg="red")

    cv.bind("<Button-1>", click)
    cv.bind("<MouseWheel>", lambda e: cv.yview_scroll(int(-e.delta / 120), "units"))
    for i in range(N):
        y0 = GAP + i * PITCH
        r = cv.create_rectangle(GAP, y0, GAP + CELL, y0 + CELL,
                                fill=FILLS[i % 4], outline="black")
        t = cv.create_text(GAP + CELL // 2, y0 + CELL // 2,
                           text="card%02d" % i, fill="black")
        items[r] = "card%02d" % i
        items[t] = "card%02d" % i
    cv.configure(scrollregion=(0, 0, CV_W, GAP + N * PITCH))
    return box, cv, cap


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    root = tk.Tk()
    root.title("Scroll/Click fix demo - karakter secimi")
    frame = tk.Frame(root)
    frame.pack(padx=8, pady=8)
    bad_box, bad_cv, bad_cap = build_gallery(frame, fixed=False)
    good_box, good_cv, good_cap = build_gallery(frame, fixed=True)
    bad_box.pack(side=tk.LEFT, padx=(0, 8))
    good_box.pack(side=tk.LEFT)
    root.update()

    # scroll so card05 (canvas y 572..672, merkez 622) widget y=100'de gozukur
    frac = (GAP + 5 * PITCH + CELL // 2 - 100) / (GAP + N * PITCH)
    for cv in (bad_cv, good_cv):
        cv.yview_moveto(frac)
    root.update()
    vtop = good_cv.canvasy(0)
    print("viewport top (canvas coords): %.1f" % vtop)

    wx, wy = 60, 100
    cx, cy = good_cv.canvasx(wx), good_cv.canvasy(wy)
    print("widget click point: (%d, %d) -> fixed canvas'te karsiligi: (%.0f, %.0f) = card05 bolgesi"
          % (wx, wy, cx, cy))

    bad_cv.event_generate("<Button-1>", x=wx, y=wy)
    good_cv.event_generate("<Button-1>", x=wx, y=wy)
    root.update()
    print("ONCE  (ham koordinat): %s" % bad_cap.cget("text"))
    print("SONRA (fix ile)      : %s" % good_cap.cget("text"))

    root.lift()
    root.update()
    bbox = (root.winfo_rootx(), root.winfo_rooty(),
            root.winfo_rootx() + root.winfo_width(), root.winfo_rooty() + root.winfo_height())
    shot = ImageGrab.grab(bbox)
    shot.save(OUT)
    print("screenshot kaydedildi: %s (%dx%d)" % (OUT, shot.size[0], shot.size[1]))

    root.after(2500, root.destroy)
    root.mainloop()
    sys.exit(0)


if __name__ == "__main__":
    main()