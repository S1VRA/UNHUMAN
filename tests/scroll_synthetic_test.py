# -*- coding: utf-8 -*-
"""Synthetic scroll/click test for the gallery canvas coordinate bug.

Proves that WITHOUT canvasx()/canvasy() the scrolled-canvas hit test selects a
WRONG item, and WITH the conversion (the fix) it selects the CORRECT item.
"""
import os
import sys
import tkinter as tk

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

N = 10
PITCH = 110  # 100x100 rect + 10 gap
AREA_H = 2000
VIEW_H = 300


def rects(cv):
    for i in range(N):
        y0 = 10 + i * PITCH
        cv.create_rectangle(10, y0, 110, y0 + 100,
                            fill=["#7bb8e6", "#e6a87b", "#8fe68f"][i % 3],
                            tags="r%d" % i, outline="black")


def which_item(cv, widget_x, widget_y, use_canvas_xy):
    if use_canvas_xy:
        x = cv.canvasx(widget_x)
        y = cv.canvasy(widget_y)
    else:
        x, y = widget_x, widget_y
    hits = cv.find_overlapping(x, y, x, y)
    for iid in reversed(hits):
        for k in range(N):
            if "r%d" % k in cv.gettags(iid):
                return k
    return None


def main():
    root = tk.Tk()
    root.withdraw()
    cv = tk.Canvas(root, width=200, height=VIEW_H, bg="white")
    rects(cv)
    cv.configure(scrollregion=(0, 0, 200, AREA_H))

    offset = 600
    max_off = AREA_H - VIEW_H
    cv.yview_moveto(offset / max_off)
    root.update_idletasks()
    print("viewport top (canvas coords): %.1f" % cv.canvasy(0))

    widget_x, widget_y = 60, 150
    cx = cv.canvasx(widget_x)
    cy = cv.canvasy(widget_y)
    print("widget point: (%d, %d) -> canvas point: (%.1f, %.1f)" % (widget_x, widget_y, cx, cy))
    expected = None
    for k in range(N):
        y0 = 10 + k * PITCH
        if y0 <= cy <= y0 + 100:
            expected = k
            print("correct item (gorsel olarak imlecin altindaki): r%d  (canvas y %d..%d)" % (k, y0, y0 + 100))

    with_fix = which_item(cv, widget_x, widget_y, True)
    without_fix = which_item(cv, widget_x, widget_y, False)
    print("RESULT  canvasx/canvasy ILE   -> item r%d" % with_fix)
    print("RESULT  ham evt koordinatiyla -> item r%d" % without_fix)

    assert with_fix is not None, "fixed path must hit something"
    assert with_fix == expected, "fixed path must select the visible card r%d" % expected
    assert without_fix != with_fix, "buggy path must select a different (wrong) item"
    print("PASS: canvasx/canvasy dogru ogeyi (r%d) seciyor; ham evt koordinati yanlis ogeyi (r%d) seciyor."
          % (with_fix, without_fix))
    root.destroy()
    sys.exit(0)


if __name__ == "__main__":
    main()