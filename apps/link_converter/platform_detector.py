"""
Módulo para detectar la plataforma y el tipo de contenido de una URL.

Returns a 4-tuple:  (nombre, icono, content_type, allow_types)
  - nombre       : str   — nombre de la plataforma
  - icono        : str | None — nombre del archivo de ícono
  - content_type : str   — tipo detectado: "video", "audio", "image", "any"
  - allow_types  : list  — tipos de descarga permitidos para esta URL
                           e.g. ["video","audio"], ["image"], ["audio"]
"""

import re

# ── Extensiones de imagen que pueden aparecer directamente en la URL ──────────
IMAGE_EXTENSIONS = (
    ".jpg", ".jpeg", ".png", ".gif", ".webp",
    ".bmp", ".tiff", ".tif", ".svg", ".avif",
)

# ── Mapeo de plataformas multimedia ──────────────────────────────────────────
# (regex_pattern, nombre, icono, content_type, allow_types)
PLATFORM_MAP = [
    # ── Solo audio ────────────────────────────────────────────────
    (r"soundcloud\.com",
     "SoundCloud",   "soundcloud.png",  "audio",  ["audio"]),

    # ── Video + audio ─────────────────────────────────────────────
    (r"(youtube\.com|youtu\.be)",
     "YouTube",      "youtube.png",     "video",  ["video", "audio"]),

    (r"tiktok\.com",
     "TikTok",       "tiktok.png",      "video",  ["video", "audio"]),

    (r"twitch\.tv",
     "Twitch",       "twitch.webp",     "video",  ["video", "audio"]),

    (r"vimeo\.com",
     "Vimeo",        "vimeo.png",       "video",  ["video", "audio"]),

    (r"(facebook\.com|fb\.com|fb\.watch)",
     "Facebook",     "facebook.png",    "video",  ["video", "audio"]),

    (r"(twitter\.com|x\.com)",
     "X / Twitter",  "x.png",           "any",    ["video", "audio", "image"]),

    # ── Imágenes ──────────────────────────────────────────────────
    (r"(imgur\.com)",
     "Imgur",        None,              "image",  ["image"]),

    (r"(pinterest\.com|pin\.it)",
     "Pinterest",    None,              "image",  ["image"]),

    # ── Instagram: puede ser video o imagen ───────────────────────
    (r"instagram\.com",
     "Instagram",    "instagram.png",   "any",    ["video", "audio", "image"]),
]


def detect_platform(url: str) -> tuple:
    """
    Detecta la plataforma y el tipo de contenido de una URL.

    Returns:
        (nombre, icono, content_type, allow_types)
        content_type: "video" | "audio" | "image" | "any"
        allow_types : lista de tipos permitidos para descargar
    """
    url_clean = url.strip()
    url_lower = url_clean.lower()

    # ── 1. Detectar por extensión de imagen directa ───────────────
    try:
        path = url_lower.split("?")[0].split("#")[0]
        if any(path.endswith(ext) for ext in IMAGE_EXTENSIONS):
            return ("Imagen directa", None, "image", ["image"])
    except Exception:
        pass

    # ── 2. Detectar por plataforma conocida ───────────────────────
    for pattern, name, icon, ctype, allow in PLATFORM_MAP:
        if re.search(pattern, url_lower):
            return (name, icon, ctype, allow)

    # ── 3. Desconocida — permitir todo ───────────────────────────
    return ("URL detectada", None, "any", ["video", "audio", "image"])


# ── Helpers de compatibilidad (usados por código viejo) ──────────────────────
def is_audio_only(url: str) -> bool:
    """True si la plataforma sólo soporta descarga de audio."""
    _, _, ctype, _ = detect_platform(url)
    return ctype == "audio"
