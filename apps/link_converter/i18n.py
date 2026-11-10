"""
apps/link_converter/i18n.py
───────────────────────────
Gestor de internacionalización ligero para MediaHub-LinkConverter.
"""

import os
import sys
import json
import locale

_CURRENT_LANG = None

STRINGS = {
    "es": {
        "app_title": "Convertidor de Links — Media Hub",
        "header_title": "Convertidor de Links",
        "header_subtitle": "Descarga de videos, audios y playlists en lote",
        "btn_add_link": "Añadir Enlace",
        "btn_clipboard": "Pegar del Portapapeles",
        "btn_download_all": "Descargar Todo",
        "btn_clear_done": "Limpiar Completados",
        "btn_exit": "Salir",
        "save_in": "Guardar en:",
        "input_placeholder": "Pega aquí uno o varios enlaces (YouTube, TikTok, Instagram, Playlists...)",
        "empty_prompt": "Pega o añade un enlace arriba para comenzar a descargar.",
    },
    "en": {
        "app_title": "Link Converter — Media Hub",
        "header_title": "Link Converter",
        "header_subtitle": "Batch video, audio and playlist downloader",
        "btn_add_link": "Add Link",
        "btn_clipboard": "Paste from Clipboard",
        "btn_download_all": "Download All",
        "btn_clear_done": "Clear Completed",
        "btn_exit": "Exit",
        "save_in": "Save to:",
        "input_placeholder": "Paste one or more links here (YouTube, TikTok, Instagram, Playlists...)",
        "empty_prompt": "Paste or add a link above to start downloading.",
    }
}


def get_current_language() -> str:
    global _CURRENT_LANG
    if _CURRENT_LANG:
        return _CURRENT_LANG

    # 1. CLI argument
    for arg in sys.argv[1:]:
        if arg.startswith("--lang="):
            val = arg.split("=", 1)[1].strip().lower()
            if val in ("es", "en"):
                _CURRENT_LANG = val
                return _CURRENT_LANG

    # 2. Environment variables
    for env_var in ("MEDIAHUB_APP_LANG", "MEDIAHUB_LANG", "LANG"):
        val = os.environ.get(env_var, "").lower()
        if val.startswith("es"):
            _CURRENT_LANG = "es"
            return "es"
        elif val.startswith("en"):
            _CURRENT_LANG = "en"
            return "en"

    # 3. Local config_lang.json
    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    for cfg in [os.path.join(base_dir, "config_lang.json"), os.path.join(base_dir, "..", "config_lang.json")]:
        if os.path.isfile(cfg):
            try:
                with open(cfg, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    val = data.get("language")
                    if val in ("es", "en"):
                        _CURRENT_LANG = val
                        return _CURRENT_LANG
            except Exception:
                pass

    # 4. Fallback sistema
    try:
        lang, _ = locale.getdefaultlocale()
        if lang and lang.lower().startswith("es"):
            _CURRENT_LANG = "es"
            return "es"
    except Exception:
        pass

    _CURRENT_LANG = "es"
    return "es"


def t(key: str, **kwargs) -> str:
    lang = get_current_language()
    text = STRINGS.get(lang, STRINGS["es"]).get(key, STRINGS["es"].get(key, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
