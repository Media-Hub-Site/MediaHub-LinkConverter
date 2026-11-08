"""
Módulo de descarga y extracción de metadatos de enlaces y playlists.
Soporta yt-dlp con extracción previa de metadatos y descargas concurrentes.
Localización y preparación automática de FFmpeg / FFprobe para post-procesado.
"""

import os
import sys
import shutil
import urllib.request
import urllib.error
from PyQt6.QtCore import QThread, pyqtSignal


def _get_ffmpeg_binary_path() -> str | None:
    """
    Localiza o prepara un ejecutable de ffmpeg / ffprobe funcional para yt-dlp.
    yt-dlp requiere que en la carpeta o binario existan 'ffmpeg.exe' y 'ffprobe.exe'.
    """
    # 1. Comprobar si ffmpeg ya está en el PATH del sistema
    for name in ("ffmpeg.exe", "ffmpeg"):
        p = shutil.which(name)
        if p and os.path.isfile(p):
            return os.path.dirname(p)

    # 2. Carpeta global compartida de Media Hub (~/.mediahub/bin)
    user_home = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    hub_bin = os.path.join(user_home, ".mediahub", "bin")
    hub_ffmpeg = os.path.join(hub_bin, "ffmpeg.exe")
    hub_ffprobe = os.path.join(hub_bin, "ffprobe.exe")
    if os.path.isfile(hub_ffmpeg) and os.path.isfile(hub_ffprobe):
        return hub_bin

    # 3. Intentar extraer/obtener desde imageio_ffmpeg
    try:
        import imageio_ffmpeg
        orig_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if orig_exe and os.path.isfile(orig_exe):
            bin_dir = os.path.dirname(orig_exe)
            ff_exe = os.path.join(bin_dir, "ffmpeg.exe")
            fp_exe = os.path.join(bin_dir, "ffprobe.exe")

            # Si se llama con sufijo (ej: ffmpeg-win-x86_64-v7.1.exe), creamos copias/enlaces
            if not os.path.isfile(ff_exe):
                try:
                    shutil.copyfile(orig_exe, ff_exe)
                except Exception:
                    pass
            if not os.path.isfile(fp_exe):
                try:
                    shutil.copyfile(orig_exe, fp_exe)
                except Exception:
                    pass

            if os.path.isfile(ff_exe):
                # También aseguramos tenerlo en ~/.mediahub/bin para futuras ejecuciones
                try:
                    os.makedirs(hub_bin, exist_ok=True)
                    if not os.path.isfile(hub_ffmpeg):
                        shutil.copyfile(orig_exe, hub_ffmpeg)
                    if not os.path.isfile(hub_ffprobe):
                        shutil.copyfile(orig_exe, hub_ffprobe)
                except Exception:
                    pass
                return bin_dir
    except Exception:
        pass

    # 4. Comprobar ~/.mediahub/bin aunque solo exista ffmpeg.exe
    if os.path.isfile(hub_ffmpeg):
        if not os.path.isfile(hub_ffprobe):
            try:
                shutil.copyfile(hub_ffmpeg, hub_ffprobe)
            except Exception:
                pass
        return hub_bin

    return None


def _parse_error(e: Exception) -> str:
    """Convierte errores de yt-dlp en mensajes legibles para el usuario."""
    msg = str(e).lower()
    original = str(e)

    if ("private" in msg and "login" in msg) or "sign in" in msg or "authentication required" in msg:
        return "Contenido privado o requiere inicio de sesión."
    if "unavailable" in msg or "not available" in msg:
        return "Video no disponible o eliminado."
    if "age" in msg and ("restrict" in msg or "confirm" in msg):
        return "Restricción de edad en la plataforma."
    if "copyright" in msg or "has been blocked" in msg:
        return "Bloqueado por derechos de autor."
    if "unsupported url" in msg or "no video formats" in msg or "unable to extract" in msg:
        return "URL no compatible o no válida."
    if "connection" in msg or "network" in msg or "timed out" in msg:
        return "Error de conexión de red."

    if len(original) > 180:
        return original[:180] + "..."
    return original


class MetadataWorker(QThread):
    """
    Extrae título, duración, miniatura y verifica si el enlace es una Playlist.
    Emite finished_info(list_of_items)
    donde cada item es dict: {url, title, uploader, duration, thumbnail_url, is_playlist}
    """
    finished_info = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self.url = url

    def run(self):
        # 1. Comprobar si es imagen directa
        clean = self.url.split("?")[0].lower()
        if clean.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):
            filename = os.path.basename(clean) or "imagen_descargada"
            item = {
                "url": self.url,
                "title": filename,
                "uploader": "Enlace Directo",
                "duration": "",
                "thumbnail_url": self.url,
                "is_playlist": False,
                "default_type": "image",
            }
            self.finished_info.emit([item])
            return

        # 2. Usar yt-dlp sin descargar para extraer info rápido
        try:
            import yt_dlp
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
                "extract_flat": "in_playlist",  # Rápido para playlists sin entrar a cada video
                "nocheckcertificate": True,
            }
            ff_loc = _get_ffmpeg_binary_path()
            if ff_loc:
                ydl_opts["ffmpeg_location"] = ff_loc

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                if not info:
                    self.error.emit("No se pudo obtener información del enlace.")
                    return

                # Si es Playlist
                if "entries" in info and info["entries"]:
                    items = []
                    playlist_title = info.get("title", "Lista de Reproducción")
                    for entry in info["entries"]:
                        if not entry:
                            continue
                        e_url = entry.get("url") or entry.get("webpage_url")
                        if not e_url and entry.get("id"):
                            e_url = f"https://www.youtube.com/watch?v={entry.get('id')}"
                        if not e_url:
                            continue

                        # Duración formateada
                        dur_s = entry.get("duration") or 0
                        dur_str = f"{int(dur_s // 60)}:{int(dur_s % 60):02d}" if dur_s else ""

                        items.append({
                            "url": e_url,
                            "title": entry.get("title", "Sin título"),
                            "uploader": entry.get("uploader") or playlist_title,
                            "duration": dur_str,
                            "thumbnail_url": entry.get("thumbnail") or "",
                            "is_playlist": False,
                            "default_type": "video",
                        })

                    if not items:
                        self.error.emit("La lista de reproducción está vacía o no tiene videos disponibles.")
                        return

                    self.finished_info.emit(items)
                    return

                # Si es un solo video / contenido
                dur_s = info.get("duration") or 0
                dur_str = f"{int(dur_s // 60)}:{int(dur_s % 60):02d}" if dur_s else ""

                item = {
                    "url": info.get("webpage_url") or self.url,
                    "title": info.get("title", "Descarga Multimedia"),
                    "uploader": info.get("uploader") or info.get("channel") or "Desconocido",
                    "duration": dur_str,
                    "thumbnail_url": info.get("thumbnail") or "",
                    "is_playlist": False,
                    "default_type": "video",
                }
                self.finished_info.emit([item])

        except Exception as e:
            self.error.emit(_parse_error(e))


class DownloadWorker(QThread):
    """
    Descarga individual de un enlace hacia la carpeta configurada.
    """
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(str, str)  # (title, saved_path)
    error = pyqtSignal(str)

    def __init__(self, url: str, output_dir: str, media_type: str = "video",
                 quality: str = "best", fmt: str = "mp4", parent=None):
        super().__init__(parent)
        self.url = url
        self.output_dir = output_dir
        self.media_type = media_type.lower()  # "video", "audio", "image"
        self.quality = quality.lower()        # "best", "1080", "720", "480", "360"
        self.fmt = fmt.lower()                # "mp4", "mkv", "mp3", "wav", "m4a", etc.
        self._is_cancelled = False
        self._last_percent = -1
        self._downloaded_title = ""
        self._final_path = ""

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        if self.media_type == "image":
            self._run_image()
        else:
            self._run_ytdlp()

    def _run_image(self):
        try:
            self.progress.emit(10, "Conectando...")
            path = self.url.split("?")[0].split("#")[0]
            raw_name = os.path.basename(path) or "imagen"
            base, _ = os.path.splitext(raw_name)
            filename = f"{base}.{self.fmt}" if self.fmt else raw_name
            dest = os.path.join(self.output_dir, filename)
            self._final_path = dest

            req = urllib.request.Request(
                self.url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                chunk = 8192
                with open(dest, "wb") as f:
                    while True:
                        if self._is_cancelled:
                            f.close()
                            if os.path.exists(dest): os.remove(dest)
                            self.error.emit("Descarga cancelada.")
                            return
                        data = resp.read(chunk)
                        if not data:
                            break
                        f.write(data)
                        downloaded += len(data)
                        if total > 0:
                            pct = min(10 + int(downloaded / total * 85), 98)
                            self.progress.emit(pct, f"Descargando {pct}%")

            self.progress.emit(100, "✅ ¡Completado!")
            self.finished.emit(filename, dest)

        except Exception as e:
            self.error.emit(str(e))

    def _run_ytdlp(self):
        try:
            import yt_dlp
        except ImportError:
            self.error.emit("yt-dlp no está instalado.")
            return

        output_template = os.path.join(self.output_dir, "%(title)s.%(ext)s")

        def progress_hook(d):
            if self._is_cancelled:
                raise Exception("Descarga cancelada por el usuario.")

            if d.get("status") == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                downloaded = d.get("downloaded_bytes", 0)
                speed = d.get("speed", 0) or 0
                pct = int(downloaded / total * 100) if total > 0 else 0

                if pct != self._last_percent:
                    self._last_percent = pct
                    spd_str = f"• {speed/1024/1024:.1f} MB/s" if speed > 0 else ""
                    self.progress.emit(pct, f"Descargando {pct}% {spd_str}")

            elif d.get("status") == "finished":
                self.progress.emit(98, "Finalizando archivo...")

        ffmpeg_location = _get_ffmpeg_binary_path()

        ydl_opts = {
            "outtmpl": output_template,
            "progress_hooks": [progress_hook],
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
        }
        if ffmpeg_location:
            ydl_opts["ffmpeg_location"] = ffmpeg_location

        if self.media_type == "audio":
            ydl_opts.update({
                "format": "bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": self.fmt,
                    "preferredquality": "192",
                }],
            })
        else:
            if self.quality == "best":
                fmt_selector = f"best[ext={self.fmt}]/best[ext=mp4]/bestvideo+bestaudio/best"
            else:
                h = self.quality
                fmt_selector = (
                    f"best[height<={h}][ext={self.fmt}]"
                    f"/best[height<={h}][ext=mp4]"
                    f"/best[height<={h}]"
                    f"/bestvideo[height<={h}]+bestaudio/best"
                )
            ydl_opts.update({
                "format": fmt_selector,
                "merge_output_format": self.fmt,
            })

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=True)
                title = info.get("title", "archivo") if info else "archivo"
                ext = info.get("ext", self.fmt) if info else self.fmt
                self._downloaded_title = title
                self._final_path = os.path.join(self.output_dir, f"{title}.{ext}")

            self.progress.emit(100, "✅ ¡Completado!")
            self.finished.emit(self._downloaded_title, self._final_path)

        except Exception as e:
            if "cancelada por el usuario" in str(e):
                self.error.emit("Descarga cancelada.")
            else:
                self.error.emit(_parse_error(e))
