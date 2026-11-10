"""
core/sound_manager.py
─────────────────────
Gestor de efectos de sonido sutiles y no invasivos para la interfaz de Media Hub.
Permite activar/silenciar sonidos y persistir la preferencia en ~/.mediahub/sound_config.json.
Usa winsound / QSoundEffect con fallback silencioso para máxima estabilidad.
"""

import os
import sys
import json
import threading

SOUND_CONFIG_FILE = os.path.join(
    os.environ.get("USERPROFILE") or os.path.expanduser("~"),
    ".mediahub",
    "sound_config.json"
)

def _get_sounds_dir():
    if getattr(sys, 'frozen', False):
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "assets", "sounds")


class SoundManager:
    _instance = None

    def __init__(self):
        self._enabled = self._load_preference()
        self._sounds_dir = _get_sounds_dir()

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = SoundManager()
        return cls._instance

    def _load_preference(self) -> bool:
        if os.path.isfile(SOUND_CONFIG_FILE):
            try:
                with open(SOUND_CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("sound_enabled", True)
            except Exception:
                pass
        return True

    def is_enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        try:
            os.makedirs(os.path.dirname(SOUND_CONFIG_FILE), exist_ok=True)
            with open(SOUND_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"sound_enabled": self._enabled}, f, indent=2)
        except Exception:
            pass

    def toggle(self) -> bool:
        self.set_enabled(not self._enabled)
        if self._enabled:
            self.play("toggle_on")
        else:
            self.play("toggle_off", force=True)
        return self._enabled

    def play(self, sound_name: str, force: bool = False):
        """
        Reproduce un sonido de forma asíncrona sin bloquear la interfaz.
        Nombres soportados: 'click', 'hover', 'success', 'toggle_on', 'toggle_off'.
        """
        if not self._enabled and not force:
            return

        sound_file = os.path.join(self._sounds_dir, f"{sound_name}.wav")
        if not os.path.isfile(sound_file):
            return

        def _play_worker():
            try:
                import winsound
                winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception:
                pass

        threading.Thread(target=_play_worker, daemon=True).start()
