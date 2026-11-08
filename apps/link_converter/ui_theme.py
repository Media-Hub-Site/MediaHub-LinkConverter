"""
apps/media_converter/ui/ui_theme.py
────────────────────────────────────
Thin shim that reads current styles from the global ThemeManager.
All constants are kept as module-level aliases so existing imports work unchanged.
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QWidget
from core.theme_manager import ThemeManager

RADIUS_LG = 18
RADIUS_MD = 12
RADIUS_SM = 10


def _tm():
    return ThemeManager.instance()


# ── Dynamic style helpers (called at widget-creation time) ───────────────────

def apply_window_theme(widget: QWidget) -> None:
    widget.setStyleSheet(_tm().app_styles()["window"])


def make_card_container() -> tuple:
    card = QFrame()
    card.setObjectName("mainCard")
    card.setStyleSheet(_tm().app_styles()["card"])
    layout = QVBoxLayout(card)
    layout.setContentsMargins(24, 24, 24, 24)
    layout.setSpacing(14)
    return card, layout


# ── Module-level aliases (re-computed each time they're accessed via getter) ─
# Because these are used as string constants at import time, we expose them
# as properties of a small proxy so they always reflect the current theme.

def _s(key: str) -> str:
    return _tm().app_styles()[key]


def _c(key: str) -> str:
    return _tm().app_colors()[key]


# Colour tokens dict (used inline in some windows with APP_COLORS["key"])
APP_COLORS = _tm().app_colors()   # snapshot; windows that need live colors call ThemeManager directly


# Style strings (these work fine because each window calls them at __init__ time)
@property
def BUTTON_STYLE():        return _s("button")
@property
def SOFT_BUTTON_STYLE():   return _s("soft_button")
@property
def REMOVE_BUTTON_STYLE(): return _s("remove_button")
@property
def CONVERT_BUTTON_STYLE():return _s("convert_button")
@property
def FFMPEG_BUTTON_STYLE(): return _s("ffmpeg_button")
@property
def COMBO_STYLE():         return _s("combo")
@property
def DROP_LABEL_STYLE():    return _s("drop_label")


# ── Plain functions (preferred – windows can call these to get current styles) ─

def get_button_style()        -> str: return _s("button")
def get_soft_button_style()   -> str: return _s("soft_button")
def get_remove_button_style() -> str: return _s("remove_button")
def get_convert_button_style()-> str: return _s("convert_button")
def get_ffmpeg_button_style() -> str: return _s("ffmpeg_button")
def get_combo_style()         -> str: return _s("combo")
def get_drop_label_style()    -> str: return _s("drop_label")
def get_app_colors()          -> dict: return _tm().app_colors()


# ── Backwards-compat string constants (light-mode values, used as fallback) ──
# Many widgets set these once at startup; they'll pick up the correct value
# because ThemeManager defaults to light mode.  When dark mode is active the
# window's __init__ runs after the toggle, so _tm() returns the dark palette.

BUTTON_STYLE        = get_button_style()
SOFT_BUTTON_STYLE   = get_soft_button_style()
REMOVE_BUTTON_STYLE = get_remove_button_style()
CONVERT_BUTTON_STYLE= get_convert_button_style()
FFMPEG_BUTTON_STYLE = get_ffmpeg_button_style()
COMBO_STYLE         = get_combo_style()
DROP_LABEL_STYLE    = get_drop_label_style()
