"""
core/theme_manager.py
─────────────────────
Singleton that stores the current dark/light preference and provides
ready-to-use style strings for every part of the app.

Usage anywhere:
    from core.theme_manager import ThemeManager
    tm = ThemeManager.instance()
    is_dark = tm.is_dark
    styles  = tm.styles()      # dict of QSS strings (hub styles)
    colors  = tm.app_colors()  # dict of color tokens (micro-app styles)
"""

from __future__ import annotations


# ──────────────────────────────────────────────────────────────────────────────
#  Color palettes
# ──────────────────────────────────────────────────────────────────────────────

_APP_COLORS_LIGHT = {
    "bg":           "#FAF7F4",
    "card":         "#FFFFFF",
    "text_main":    "#4B362D",
    "text_muted":   "#7A5A49",
    "border":       "#E9D8CD",
    "accent":       "#E7BFA7",
    "accent_hover": "#DFAE90",
    "accent_soft":  "#F8EEE8",
    "drop_bg":      "#FCF6F1",
}

_APP_COLORS_DARK = {
    "bg":           "#141420",
    "card":         "#1E1E2E",
    "text_main":    "#E4E0DC",
    "text_muted":   "#9898B8",
    "border":       "#2E2E45",
    "accent":       "#6C63FF",
    "accent_hover": "#7C73FF",
    "accent_soft":  "#252535",
    "drop_bg":      "#1A1A2A",
}

# ──────────────────────────────────────────────────────────────────────────────
#  Hub-level palettes (used by hub_theme.py)
# ──────────────────────────────────────────────────────────────────────────────

_HUB_LIGHT = {
    "window_bg":        "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0B1D3A, stop:1 #133D7A)",
    "card_bg":          "#F8F9FB",
    "card_disabled_bg": "#D3D8DE",
    "card_title":       "#1A1A1A",
    "card_subtitle":    "#555555",
    "portable_label":   "#888888",
    "toggle_bg":        "rgba(255,255,255,0.15)",
    "toggle_bg_hover":  "rgba(255,255,255,0.28)",
    "toggle_border":    "rgba(255,255,255,0.35)",
    "toggle_color":     "#FFFFFF",
    "btn_open_bg":      "#0069D9",
    "btn_open_hover":   "#007BFF",
    "btn_open_press":   "#0062CC",
    "btn_install_bg":   "#218838",
    "btn_install_hover":"#28A745",
    "btn_install_press":"#1E7E34",
    "btn_disabled_bg":  "#A0A5AA",
    "btn_disabled_fg":  "#444444",
}

_HUB_DARK = {
    "window_bg":        "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0A0A0F, stop:1 #12121E)",
    "card_bg":          "#1E1E2E",
    "card_disabled_bg": "#2A2A3A",
    "card_title":       "#E8E8F0",
    "card_subtitle":    "#9090A8",
    "portable_label":   "#6060A0",
    "toggle_bg":        "rgba(255,220,80,0.15)",
    "toggle_bg_hover":  "rgba(255,220,80,0.28)",
    "toggle_border":    "rgba(255,220,80,0.45)",
    "toggle_color":     "#FFE066",
    "btn_open_bg":      "#3B5EFF",
    "btn_open_hover":   "#5577FF",
    "btn_open_press":   "#2244EE",
    "btn_install_bg":   "#1A6B3A",
    "btn_install_hover":"#22884A",
    "btn_install_press":"#145230",
    "btn_disabled_bg":  "#2E2E3E",
    "btn_disabled_fg":  "#666680",
}


# ──────────────────────────────────────────────────────────────────────────────
#  Style generators
# ──────────────────────────────────────────────────────────────────────────────

RADIUS_LG = 18
RADIUS_MD = 12
RADIUS_SM = 10


def _build_app_styles(c: dict) -> dict:
    """Build all micro-app QSS strings from a color dict `c`."""

    window_style = f"""
        QWidget {{
            background-color: {c["bg"]};
            color: {c["text_main"]};
            font-family: "Segoe UI", "Inter", sans-serif;
        }}
        QLabel {{
            background: transparent;
        }}
        QMessageBox {{
            background-color: {c["bg"]};
        }}
        QMessageBox QPushButton {{
            background: {c["accent_soft"]};
            border: 1px solid {c["border"]};
            border-radius: {RADIUS_SM}px;
            padding: 8px 14px;
            font-weight: 600;
            min-width: 90px;
        }}
        QProgressDialog {{
            background: {c["bg"]};
            border: 1px solid {c["border"]};
            border-radius: {RADIUS_MD}px;
        }}
        QProgressBar {{
            background: {c["card"]};
            border: 1px solid {c["border"]};
            border-radius: {RADIUS_SM}px;
            min-height: 10px;
            text-align: center;
            color: {c["text_main"]};
        }}
        QProgressBar::chunk {{
            background: {c["accent"]};
            border-radius: {RADIUS_SM}px;
        }}
    """

    card_style = f"""
        QFrame#mainCard {{
            background: {c["card"]};
            border: 1px solid {c["border"]};
            border-radius: {RADIUS_LG}px;
        }}
    """

    button = (
        f"QPushButton{{background:{c['accent']};color:{c['text_main']};"
        f"padding:10px 12px;border-radius:{RADIUS_MD}px;border:1px solid {c['border']};font-weight:600;}}"
        f"QPushButton:hover{{background:{c['accent_hover']};}}"
        f"QPushButton:pressed{{background:{c['accent']};}}"
        f"QPushButton:disabled{{background:{c['accent_soft']};color:{c['text_muted']};}}"
    )

    soft_button = (
        f"QPushButton{{background:{c['accent_soft']};color:{c['text_main']};"
        f"padding:8px 10px;border-radius:{RADIUS_MD}px;border:1px solid {c['border']};font-weight:600;}}"
        f"QPushButton:hover{{background:{c['accent_soft']};}}"
        f"QPushButton:pressed{{background:{c['card']};}}"
    )

    remove_button = (
        f"QPushButton{{background:#FF684D;color:#FFFFFF;"
        f"padding:10px 12px;border-radius:{RADIUS_MD}px;border:1px solid #D0553F;font-weight:600;}}"
        f"QPushButton:hover{{background:#FF856E;}}"
        f"QPushButton:pressed{{background:#E05A42;}}"
        f"QPushButton:disabled{{background:{c['accent_soft']};color:{c['text_muted']};border:1px solid {c['border']};}}"
    )

    convert_button = (
        f"QPushButton{{background:#2ECC71;color:#0D3320;"
        f"padding:10px 12px;border-radius:{RADIUS_MD}px;border:1px solid #27AE60;font-weight:600;}}"
        f"QPushButton:hover{{background:#3DDA80;}}"
        f"QPushButton:pressed{{background:#25A35A;}}"
        f"QPushButton:disabled{{background:{c['accent_soft']};color:{c['text_muted']};border:1px solid {c['border']};}}"
    )

    ffmpeg_button = (
        f"QPushButton{{background:#D0553F;color:#FFFFFF;"
        f"padding:8px 10px;border-radius:{RADIUS_MD}px;border:1px solid #A8412D;font-weight:600;}}"
        f"QPushButton:hover{{background:#E0644D;}}"
        f"QPushButton:pressed{{background:#B54632;}}"
    )

    combo = (
        f"QComboBox{{background:{c['card']};border:1px solid {c['border']};padding:6px;"
        f"border-radius:{RADIUS_SM}px;color:{c['text_main']};min-height:18px;}}"
        f"QComboBox:hover{{border:1px solid {c['accent']};}}"
        f"QComboBox:focus{{border:1px solid {c['accent']};}}"
        f"QComboBox::drop-down{{border:none;padding-right:6px;}}"
        f"QComboBox QAbstractItemView{{background:{c['card']};border:1px solid {c['border']};"
        f"selection-background-color:{c['accent_soft']};selection-color:{c['text_main']};}}"
    )

    drop_label = (
        f"background: {c['drop_bg']};"
        f"border: 2px dashed {c['border']};"
        f"color: {c['text_muted']};"
        "padding: 12px;"
        f"border-radius: {RADIUS_MD}px;"
    )

    # Document-converter inner button style
    doc_btn = f"""
        QPushButton {{
            background-color: {c['card']};
            border: 1px solid {c['border']};
            border-radius: 8px;
            padding: 12px 20px;
            text-align: left;
            font-size: 11pt;
            font-weight: bold;
            color: {c['text_main']};
        }}
        QPushButton:hover {{
            background-color: {c['accent_soft']};
            border: 1px solid {c['accent']};
        }}
        QPushButton:pressed {{
            background-color: {c['accent_soft']};
        }}
    """

    return {
        "window":         window_style,
        "card":           card_style,
        "button":         button,
        "soft_button":    soft_button,
        "remove_button":  remove_button,
        "convert_button": convert_button,
        "ffmpeg_button":  ffmpeg_button,
        "combo":          combo,
        "drop_label":     drop_label,
        "doc_btn":        doc_btn,
    }


def _build_hub_styles(h: dict) -> dict:
    """Build hub QSS strings from a hub color dict `h`."""

    window = f"QMainWindow {{ background: {h['window_bg']}; }}"

    title = """
        QLabel#hubTitle {
            color: white;
            font-size: 24pt;
            font-weight: bold;
            font-family: "Segoe UI", "Arial", sans-serif;
        }
    """

    card_normal = f"QFrame#appCard {{ background-color: {h['card_bg']}; border-radius: 12px; }}"
    card_disabled = f"QFrame#appCardDisabled {{ background-color: {h['card_disabled_bg']}; border-radius: 12px; }}"

    card_title = f"""
        QLabel {{
            color: {h['card_title']};
            font-size: 16pt;
            font-weight: 900;
            font-family: "Segoe UI", "Arial", sans-serif;
        }}
    """

    card_subtitle = f"""
        QLabel {{
            color: {h['card_subtitle']};
            font-size: 10pt;
            font-family: "Segoe UI", "Arial", sans-serif;
        }}
    """

    btn_install = f"""
        QPushButton {{
            background-color: {h['btn_install_bg']}; color: white; border: none;
            border-radius: 6px; padding: 8px 16px; font-weight: bold; font-size: 11pt;
        }}
        QPushButton:hover  {{ background-color: {h['btn_install_hover']}; }}
        QPushButton:pressed {{ background-color: {h['btn_install_press']}; }}
    """

    btn_open = f"""
        QPushButton {{
            background-color: {h['btn_open_bg']}; color: white; border: none;
            border-radius: 6px; padding: 8px 16px; font-weight: bold; font-size: 11pt;
        }}
        QPushButton:hover  {{ background-color: {h['btn_open_hover']}; }}
        QPushButton:pressed {{ background-color: {h['btn_open_press']}; }}
    """

    btn_disabled = f"""
        QPushButton {{
            background-color: {h['btn_disabled_bg']}; color: {h['btn_disabled_fg']}; border: none;
            border-radius: 6px; padding: 8px 16px; font-weight: bold; font-size: 11pt;
        }}
    """

    portable = f"QLabel {{ color: {h['portable_label']}; font-weight: bold; font-size: 10pt; }}"

    toggle = f"""
        QPushButton {{
            background-color: {h['toggle_bg']};
            color: {h['toggle_color']};
            border: 1.5px solid {h['toggle_border']};
            border-radius: 18px;
            padding: 6px 18px;
            font-size: 13pt;
            font-weight: bold;
        }}
        QPushButton:hover  {{ background-color: {h['toggle_bg_hover']}; }}
        QPushButton:pressed {{ background-color: {h['toggle_bg']}; }}
    """

    return {
        "window":       window,
        "title":        title,
        "card_normal":  card_normal,
        "card_disabled":card_disabled,
        "card_title":   card_title,
        "card_subtitle":card_subtitle,
        "btn_install":  btn_install,
        "btn_open":     btn_open,
        "btn_disabled": btn_disabled,
        "portable":     portable,
        "toggle_btn":   toggle,
    }


# ──────────────────────────────────────────────────────────────────────────────
#  ThemeManager singleton
# ──────────────────────────────────────────────────────────────────────────────

class ThemeManager:
    _inst: "ThemeManager | None" = None

    def __init__(self):
        self._dark = False

    @classmethod
    def instance(cls) -> "ThemeManager":
        if cls._inst is None:
            cls._inst = cls()
        return cls._inst

    # ── State ────────────────────────────────────────────────────────────────
    @property
    def is_dark(self) -> bool:
        return self._dark

    def set_dark(self, value: bool) -> None:
        self._dark = value

    def toggle(self) -> bool:
        self._dark = not self._dark
        return self._dark

    # ── Style accessors ──────────────────────────────────────────────────────
    def hub_styles(self) -> dict:
        """Return hub-level QSS dict."""
        return _build_hub_styles(_HUB_DARK if self._dark else _HUB_LIGHT)

    def app_styles(self) -> dict:
        """Return micro-app QSS dict."""
        return _build_app_styles(_APP_COLORS_DARK if self._dark else _APP_COLORS_LIGHT)

    def app_colors(self) -> dict:
        """Return the raw color tokens dict for micro-apps."""
        return _APP_COLORS_DARK if self._dark else _APP_COLORS_LIGHT
