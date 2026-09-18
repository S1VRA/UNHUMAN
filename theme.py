import tkinter as tk
from tkinter import ttk


def apply_obsidian_theme(root):
    """Apply the Obsidian dark theme to the given root window.

    Returns the ttk.Style instance for further customization.
    """
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception as e:
        print(f"Theme warning: could not set clam theme: {e}")

    # ── Core colors ──────────────────────────────────────────────
    _bg = "#0D0E12"          # root/obsidian
    _card = "#16181F"        # card / panel
    _border = "#22252E"      # card border
    _text = "#E6E8EF"        # primary text
    _muted = "#8A90A2"       # secondary text
    _accent = "#4F8CFF"      # accent
    _accent_hover = "#3A6FE0"
    _accent_pressed = "#3A6FE0"
    _danger = "#FF5C5C"
    _warning = "#FFB020"
    _success = "#3DDC84"
    _disabled = "#2A2E3A"
    _disabled_text = "#6A7080"

    # ── Root background ──────────────────────────────────────────
    root.configure(bg=_bg)

    # ── General style configs ────────────────────────────────────
    style.configure(".", background=_bg, foreground=_text, font=("Segoe UI", 10))

    # ── Obsidian.TFrame ─────────────────────────────────────────
    style.configure("Obsidian.TFrame", background=_bg)

    # ── Card.TFrame ─────────────────────────────────────────────
    style.configure(
        "Card.TFrame",
        background=_card,
        relief="flat",
        borderwidth=0,
    )

    # ── Card.TLabel ─────────────────────────────────────────────
    style.configure("Card.TLabel", background=_card, foreground=_text)

    # ── Muted.TLabel ────────────────────────────────────────────
    style.configure("Muted.TLabel", background=_card, foreground=_muted)

    # ── Title.TLabel ────────────────────────────────────────────
    style.configure(
        "Title.TLabel",
        background=_bg,
        foreground=_text,
        font=("Segoe UI Semibold", 18),
    )

    # ── Subtitle.TLabel ─────────────────────────────────────────
    style.configure(
        "Subtitle.TLabel",
        background=_bg,
        foreground=_muted,
        font=("Segoe UI", 10),
    )

    # ── Accent.TButton ──────────────────────────────────────────
    style.configure(
        "Accent.TButton",
        background=_accent,
        foreground="#FFFFFF",
        borderwidth=0,
        focuscolor="none",
        padding=(16, 10),
    )
    style.map(
        "Accent.TButton",
        background=[("active", _accent_hover), ("pressed", _accent_pressed), ("disabled", _disabled)],
        foreground=[("disabled", _disabled_text)],
    )

    # ── Ghost.TButton ───────────────────────────────────────────
    style.configure(
        "Ghost.TButton",
        background=_card,
        foreground=_text,
        borderwidth=0,
        padding=(14, 9),
    )
    style.map(
        "Ghost.TButton",
        background=[("active", _border), ("pressed", _border)],
    )

    # ── Danger.TButton ──────────────────────────────────────────
    style.configure(
        "Danger.TButton",
        background=_danger,
        foreground="#FFFFFF",
        borderwidth=0,
        padding=(14, 9),
    )
    style.map(
        "Danger.TButton",
        background=[("active", "#E04848")],
    )

    # ── Obsidian.TEntry ─────────────────────────────────────────
    style.configure(
        "Obsidian.TEntry",
        fieldbackground=_card,
        foreground=_text,
        bordercolor=_border,
        insertcolor=_text,
        padding=8,
    )

    # ── Obsidian.TCombobox ──────────────────────────────────────
    style.configure(
        "Obsidian.TCombobox",
        fieldbackground=_card,
        background=_card,
        foreground=_text,
        arrowcolor=_muted,
        bordercolor=_border,
        padding=6,
    )

    # ── Obsidian.Treeview ───────────────────────────────────────
    style.configure(
        "Obsidian.Treeview",
        background=_card,
        fieldbackground=_card,
        foreground=_text,
        rowheight=30,
        borderwidth=0,
        font=("Segoe UI", 10),
    )

    # ── Obsidian.Treeview.Heading ───────────────────────────────
    style.configure(
        "Obsidian.Treeview.Heading",
        background=_bg,
        foreground=_muted,
        relief="flat",
        font=("Segoe UI Semibold", 10),
    )

    # ── Obsidian.Treeview map (selected row) ────────────────────
    style.map(
        "Obsidian.Treeview",
        background=[("selected", _accent)],
        foreground=[("selected", "#FFFFFF")],
    )

    # ── Obsidian.Vertical.TScrollbar ────────────────────────────
    style.configure(
        "Obsidian.Vertical.TScrollbar",
        background=_border,
        troughcolor=_bg,
        bordercolor=_bg,
        arrowcolor=_muted,
    )

    # ── Apply to root ────────────────────────────────────────────
    try:
        root.configure(bg=_bg)
    except tk.TclError:
        pass

    return style