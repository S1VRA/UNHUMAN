"""Unified theme tokens and ttk style setup for NH Mod Tool.

Colors, typography and spacing live here as the single source of truth
(``PALETTE``, ``TYPOGRAPHY``, ``SPACING``). NHModTool.py reads these
tokens for its tk/canvas widgets while the ttk UI uses ttkbootstrap
themes (darkly), so the color story stays unified.

RADIUS: ttk does not support rounded corners. Button "radius" is only the
padding/borderwidth of the underlying clam theme, so no radius token exists.
"""

# ── Color palette (Dark — defaults) ───────────────────────────────
PALETTE = {
    # Surfaces
    "bg.base": "#0D0E12",
    "bg.surface": "#16181F",
    "bg.elevated": "#1C1F28",
    "bg.overlay": "#22252E",
    "bg.footer": "#141926",
    "bg.menu": "#0D0E12",
    # Text
    "text.primary": "#F3F4F6",
    "text.secondary": "#C5C9D4",
    "text.muted": "#8A90A2",
    "text.inverse": "#FFFFFF",
    # Borders
    "border.subtle": "#2A2D3A",
    "border.default": "#2E3140",
    "border.focus": "#60A5FA",
    # Accent
    "accent.primary": "#3B82F6",
    "accent.hover": "#60A5FA",
    "accent.pressed": "#1D4ED8",
    "accent.subtle": "#1E2A44",
    "accent.solid": "#2563EB",
    "accent.solid_hover": "#1D4ED8",
    "accent.solid_pressed": "#1E40AF",
    # States (base + subtle bg + dedicated text)
    "state.success": "#3DDC84",
    "state.success_bg": "#123524",
    "state.success_text": "#3DDC84",
    "state.warning": "#FFB020",
    "state.warning_bg": "#3A2A0E",
    "state.warning_text": "#FFB020",
    "state.danger": "#FF5C5C",
    "state.danger_bg": "#3A1416",
    "state.danger_text": "#FF5C5C",
    "state.danger_solid": "#B91C1C",
    "state.danger_hover": "#A11C1C",
    "state.danger_pressed": "#7F1515",
    "state.info": "#60A5FA",
    "state.info_bg": "#12243D",
    "state.info_text": "#60A5FA",
    # Disabled
    "disabled.bg": "#22252E",
    "disabled.text": "#59607A",
    # Mockup hedef tasarım renk dili (menü vurgusu + kart tonları)
    "accent.teal": "#2DD4BF",
    "menu.passive_bg": "#181B22",
    "menu.passive_fg": "#9AA0AE",
    "menu.active_bg": "#0F3439",
    "menu.active_fg": "#E8FBF9",
    "card.photo": "#A78BFA",
    "card.photo_bg": "#191026",
    "card.pack": "#818CF8",
    "card.pack_bg": "#12172B",
    "card.manager": "#2DD4BF",
    "card.manager_bg": "#0E211F",
    "card.chart": "#F472B6",
    "card.chart_bg": "#211320",
    "panel.status_bg": "#0F2B33",
    "panel.status_border": "#2DD4BF",
    # Extra: checkerboard + gallery cell fixed palette
    "checker.light": "#3C3C3C",
    "checker.dark": "#505050",
    "gallery.cell_norm": "#1D2230",
    "gallery.cell_sel": "#171B26",
}

# ── Typography (tk pt scale; 10pt base) ───────────────────────────
# Each size token is a (family, size, weight) tuple usable by ttk styles.
TYPOGRAPHY = {
    "family": "Segoe UI",
    "mono_family": "Consolas",
    "fallback_family": "TkDefaultFont",
    "display": ("Segoe UI", 24, "bold"),
    "h1": ("Segoe UI", 17, "bold"),
    "h2": ("Segoe UI", 13, "bold"),
    "h3": ("Segoe UI", 11, "bold"),
    "body": ("Segoe UI", 10, "normal"),
    "small": ("Segoe UI", 9, "normal"),
    "mono": ("Consolas", 10, "normal"),
}

# ── Spacing (4px grid) ────────────────────────────────────────────
SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 24,
    "2xl": 32,
}
