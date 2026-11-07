"""
Worker de descarga en hilo separado.
  - Video / Audio : usa yt-dlp
  - Imagen        : descarga directa vía urllib
"""

import os
import urllib.request
import urllib.error
from PyQt6.QtCore import QThread, pyqtSignal


def _parse_error(e: Exception) -> str:
    """Convierte errores de yt-dlp en mensajes legibles."""
    msg = str(e).lower()
    original = str(e)

    if (("private" in msg and "login" in msg)
            or "sign in" in msg or "authentication required" in msg):
        return "Este contenido es privado o requiere inicio de sesión."
    if "unavailable" in msg or "not available" in msg:
        return "Este video no está disponible en tu región o fue eliminado."
    if "age" in msg and ("restrict" in msg or "confirm" in msg):
        return "Este contenido tiene restricción de edad."
    if "copyright" in msg or "has been blocked" in msg:
        return "Este contenido está bloqueado por derechos de autor."
    if ("unsupported url" in msg or "no video formats" in msg
            or "unable to extract" in msg):
        return "La URL no es válida o no es compatible con ninguna plataforma soportada."
    if "connection" in msg or "network" in msg or "timed out" in msg:
        return "No se pudo conectar. Verifica tu conexión a internet e intenta de nuevo."

    if len(original) > 300:
        return original[:300] + "..."
    return original


# ─────────────────────────────────────────────────────────────────────────────
#  Worker para VIDEO / AUDIO  (yt-dlp)
# ─────────────────────────────────────────────────────────────────────────────
class DownloadWorker(QThread):
    """Hilo de descarga multimedia. Emite señales de progreso, fin y error."""

    progress = pyqtSignal(int, str)   # (porcentaje 0-100, texto_estado)
    finished = pyqtSignal(str)         # título del archivo descargado
    error    = pyqtSignal(str)         # mensaje de error legible

    def __init__(self, url: str, media_type: str, fmt: str,
                 quality: str, output_dir: str, parent=None):
        super().__init__(parent)
        self.url        = url
        self.media_type = media_type   # "video" | "audio" | "image"
        self.fmt        = fmt
        self.quality    = quality
        self.output_dir = output_dir
        self._last_percent        = -1
        self._download_completed  = False
        self._downloaded_title    = "archivo"

    # ── dispatch ─────────────────────────────────────────────────────────────
    def run(self):
        if self.media_type == "image":
            self._run_image()
        else:
            self._run_ytdlp()

    # ── Image download ────────────────────────────────────────────────────────
    def _run_image(self):
        """Descarga una imagen directamente desde su URL."""
        try:
            self.progress.emit(10, "Conectando...")

            # Determinar nombre de archivo
            path = self.url.split("?")[0].split("#")[0]
            raw_name = os.path.basename(path) or "imagen"

            # Asegurarnos de que el nombre termina en la extensión elegida
            base, _ = os.path.splitext(raw_name)
            filename = f"{base}.{self.fmt}" if self.fmt else raw_name

            dest = os.path.join(self.output_dir, filename)

            self.progress.emit(30, "Descargando imagen...")

            req = urllib.request.Request(
                self.url,
                headers={"User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/120 Safari/537.36"
                )}
            )

            with urllib.request.urlopen(req, timeout=30) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                chunk = 8192
                with open(dest, "wb") as f:
                    while True:
                        data = resp.read(chunk)
                        if not data:
                            break
                        f.write(data)
                        downloaded += len(data)
                        if total > 0:
                            pct = min(30 + int(downloaded / total * 65), 95)
                            self.progress.emit(pct, f"Descargando... {pct}%")

            self.progress.emit(100, "✅ ¡Descarga completada!")
            self.finished.emit(filename)

        except urllib.error.HTTPError as e:
            self.error.emit(f"Error HTTP {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            self.error.emit(f"No se pudo conectar: {e.reason}")
        except Exception as e:
            self.error.emit(str(e))

    # ── Video / Audio download (yt-dlp) ───────────────────────────────────────
    def _run_ytdlp(self):
        try:
            import yt_dlp
        except ImportError:
            self.error.emit("yt-dlp no está instalado. Ejecuta: pip install yt-dlp")
            return

        output_template = os.path.join(self.output_dir, "%(title)s.%(ext)s")

        def progress_hook(d):
            if d.get("status") == "downloading":
                total      = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                downloaded = d.get("downloaded_bytes", 0)
                speed      = d.get("speed", 0) or 0
                percent    = int(downloaded / total * 100) if total > 0 else 0

                if percent != self._last_percent:
                    self._last_percent = percent
                    spd = f"{speed/1024/1024:.1f} MB/s" if speed > 0 else ""
                    self.progress.emit(percent, f"Descargando... {percent}% {spd}")

            elif d.get("status") == "finished":
                self._download_completed = True
                self.progress.emit(99, "Procesando archivo...")

        # ffmpeg bundled
        ffmpeg_location = None
        try:
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            if os.path.isfile(ffmpeg_exe):
                ffmpeg_location = os.path.dirname(ffmpeg_exe)
        except Exception:
            pass

        ydl_opts = {
            "outtmpl":          output_template,
            "progress_hooks":   [progress_hook],
            "quiet":            True,
            "no_warnings":      True,
            "nocheckcertificate": True,
        }
        if ffmpeg_location:
            ydl_opts["ffmpeg_location"] = ffmpeg_location

        if self.media_type == "audio":
            ydl_opts.update({
                "format": "bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio/best",
                "postprocessors": [{
                    "key":             "FFmpegExtractAudio",
                    "preferredcodec":  self.fmt,
                    "preferredquality": "192",
                }],
            })
        else:
            if self.quality == "best":
                fmt_selector = (
                    f"best[ext={self.fmt}]"
                    f"/best[ext=mp4]"
                    f"/bestvideo+bestaudio/best"
                )
            else:
                h = self.quality
                fmt_selector = (
                    f"best[height<={h}][ext={self.fmt}]"
                    f"/best[height<={h}][ext=mp4]"
                    f"/best[height<={h}]"
                    f"/bestvideo[height<={h}]+bestaudio"
                    f"/best"
                )
            ydl_opts.update({
                "format":              fmt_selector,
                "merge_output_format": self.fmt,
            })

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=True)
                title = info.get("title", "archivo") if info else "archivo"
                self._downloaded_title   = title
                self._download_completed = True

            self.progress.emit(100, "✅ ¡Descarga completada!")
            self.finished.emit(self._downloaded_title)

        except Exception as e:
            if self._download_completed:
                self.progress.emit(100, "✅ ¡Descarga completada!")
                self.finished.emit(self._downloaded_title)
            else:
                self.error.emit(_parse_error(e))
