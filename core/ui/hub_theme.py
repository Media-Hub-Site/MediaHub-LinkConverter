# ────────────────────────────────────────────────────────────────
#  hub_theme.py  –  Light & Dark theme definitions for Media Hub
# ────────────────────────────────────────────────────────────────

# ── LIGHT MODE ──────────────────────────────────────────────────
LIGHT = {
    "window_bg":       "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0B1D3A, stop:1 #133D7A)",
    "card_bg":         "#F8F9FB",
    "card_disabled_bg":"#D3D8DE",
    "card_title":      "#1A1A1A",
    "card_subtitle":   "#555555",
    "portable_label":  "#888888",
    "toggle_bg":       "rgba(255,255,255,0.15)",
    "toggle_bg_hover": "rgba(255,255,255,0.28)",
    "toggle_border":   "rgba(255,255,255,0.35)",
    "toggle_color":    "#FFFFFF",
    "btn_open_bg":     "#0069D9",
    "btn_open_hover":  "#007BFF",
    "btn_open_press":  "#0062CC",
    "btn_install_bg":  "#218838",
    "btn_install_hover":"#28A745",
    "btn_install_press":"#1E7E34",
    "btn_disabled_bg": "#A0A5AA",
    "btn_disabled_fg": "#444444",
}

# ── DARK MODE ───────────────────────────────────────────────────
DARK = {
    "window_bg":       "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0A0A0F, stop:1 #12121E)",
    "card_bg":         "#1E1E2E",
    "card_disabled_bg":"#2A2A3A",
    "card_title":      "#E8E8F0",
    "card_subtitle":   "#9090A8",
    "portable_label":  "#6060A0",
    "toggle_bg":       "rgba(255,220,80,0.15)",
    "toggle_bg_hover": "rgba(255,220,80,0.28)",
    "toggle_border":   "rgba(255,220,80,0.45)",
    "toggle_color":    "#FFE066",
    "btn_open_bg":     "#3B5EFF",
    "btn_open_hover":  "#5577FF",
    "btn_open_press":  "#2244EE",
    "btn_install_bg":  "#1A6B3A",
    "btn_install_hover":"#22884A",
    "btn_install_press":"#145230",
    "btn_disabled_bg": "#2E2E3E",
    "btn_disabled_fg": "#666680",
}


def get_styles(theme: dict) -> dict:
    """Return a dict of all QSS strings for the given theme dict."""

    window_style = f"""
        QMainWindow {{
            background: {theme["window_bg"]};
        }}
    """

    title_style = """
        QLabel#hubTitle {
            color: white;
            font-size: 24pt;
            font-weight: bold;
            font-family: "Segoe UI", "Arial", sans-serif;
        }
    """

    card_normal = f"""
        QFrame#appCard {{
            background-color: {theme["card_bg"]};
            border-radius: 12px;
        }}
    """

    card_disabled = f"""
        QFrame#appCardDisabled {{
            background-color: {theme["card_disabled_bg"]};
            border-radius: 12px;
        }}
    """

    card_title = f"""
        QLabel {{
            color: {theme["card_title"]};
            font-size: 16pt;
            font-weight: 900;
            font-family: "Segoe UI", "Arial", sans-serif;
        }}
    """

    card_subtitle = f"""
        QLabel {{
            color: {theme["card_subtitle"]};
            font-size: 10pt;
            font-family: "Segoe UI", "Arial", sans-serif;
        }}
    """

    btn_install = f"""
        QPushButton {{
            background-color: {theme["btn_install_bg"]};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: bold;
            font-size: 11pt;
        }}
        QPushButton:hover  {{ background-color: {theme["btn_install_hover"]}; }}
        QPushButton:pressed {{ background-color: {theme["btn_install_press"]}; }}
    """

    btn_open = f"""
        QPushButton {{
            background-color: {theme["btn_open_bg"]};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: bold;
            font-size: 11pt;
        }}
        QPushButton:hover  {{ background-color: {theme["btn_open_hover"]}; }}
        QPushButton:pressed {{ background-color: {theme["btn_open_press"]}; }}
    """

    btn_disabled = f"""
        QPushButton {{
            background-color: {theme["btn_disabled_bg"]};
            color: {theme["btn_disabled_fg"]};
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: bold;
            font-size: 11pt;
        }}
    """

    portable_label = f"""
        QLabel {{
            color: {theme["portable_label"]};
            font-weight: bold;
            font-size: 10pt;
        }}
    """

    toggle_btn = f"""
        QPushButton {{
            background-color: {theme["toggle_bg"]};
            color: {theme["toggle_color"]};
            border: 1.5px solid {theme["toggle_border"]};
            border-radius: 18px;
            padding: 6px 18px;
            font-size: 13pt;
            font-weight: bold;
        }}
        QPushButton:hover  {{ background-color: {theme["toggle_bg_hover"]}; }}
        QPushButton:pressed {{ background-color: {theme["toggle_bg"]}; }}
    """

    return {
        "window":       window_style,
        "title":        title_style,
        "card_normal":  card_normal,
        "card_disabled":card_disabled,
        "card_title":   card_title,
        "card_subtitle":card_subtitle,
        "btn_install":  btn_install,
        "btn_open":     btn_open,
        "btn_disabled": btn_disabled,
        "portable":     portable_label,
        "toggle_btn":   toggle_btn,
    }


# ── Convenience pre-built style sets ────────────────────────────
LIGHT_STYLES = get_styles(LIGHT)
DARK_STYLES  = get_styles(DARK)

# Legacy aliases (keep backward-compat for anything still importing these)
HUB_WINDOW_STYLE    = LIGHT_STYLES["window"]
HUB_TITLE_STYLE     = LIGHT_STYLES["title"]
CARD_STYLE_NORMAL   = LIGHT_STYLES["card_normal"]
CARD_STYLE_DISABLED = LIGHT_STYLES["card_disabled"]
CARD_TITLE_STYLE    = LIGHT_STYLES["card_title"]
CARD_SUBTITLE_STYLE = LIGHT_STYLES["card_subtitle"]
BTN_INSTALL_STYLE   = LIGHT_STYLES["btn_install"]
BTN_OPEN_STYLE      = LIGHT_STYLES["btn_open"]
BTN_DISABLED_STYLE  = LIGHT_STYLES["btn_disabled"]
PORTABLE_LABEL_STYLE= LIGHT_STYLES["portable"]
