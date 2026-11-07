import os
import subprocess
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QProgressBar, QFileDialog,
    QMessageBox, QApplication, QFrame
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

from apps.link_converter.platform_detector import detect_platform
from apps.media_converter.ui.ui_theme import (
    get_app_colors, get_soft_button_style,
    apply_window_theme, make_card_container,
)

# ── Estilos fijos del Link Converter (colores propios tipo "terminal") ────────
URL_INPUT_STYLE = """
    QLineEdit {
        background-color: #1e1e2a;
        color: #ffffff;
        border: 2px solid #3a3a52;
        border-radius: 10px;
        padding: 10px 14px;
        font-size: 11pt;
        font-family: 'Segoe UI', sans-serif;
    }
    QLineEdit:focus {
        border-color: #6c63ff;
    }
    QLineEdit::placeholder {
        color: #666;
    }
"""

TYPE_BTN_ACTIVE = """
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            from:#6c63ff, to:#a78bfa);
        color: white;
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 11pt;
        font-weight: bold;
        border: none;
    }
"""

# Imagen activa: degradado verde-azulado
TYPE_BTN_ACTIVE_IMG = """
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            from:#11998e, to:#38ef7d);
        color: white;
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 11pt;
        font-weight: bold;
        border: none;
    }
"""

TYPE_BTN_INACTIVE_TMPL = """    QPushButton {{
        background-color: #2b2b3b;
        color: {muted};
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 11pt;
        border: 2px solid #3a3a52;
    }}
    QPushButton:hover {{
        background-color: #35354a;
        color: white;
    }}
"""

TYPE_BTN_DISABLED = """
    QPushButton {
        background-color: #1e1e2a;
        color: #444;
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 11pt;
        border: 2px solid #2a2a3a;
    }
"""

COMBO_STYLE_LC = """
    QComboBox {
        background-color: #1e1e2a;
        color: white;
        border: 2px solid #3a3a52;
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 10pt;
        min-width: 120px;
    }
    QComboBox:hover { border-color: #6c63ff; }
    QComboBox::drop-down {
        border: none;
        padding-right: 10px;
    }
    QComboBox QAbstractItemView {
        background-color: #1e1e2a;
        color: white;
        selection-background-color: #6c63ff;
        border: 1px solid #3a3a52;
        border-radius: 6px;
    }
"""

PROGRESS_STYLE = """
    QProgressBar {
        background-color: #1e1e2a;
        border: 2px solid #3a3a52;
        border-radius: 8px;
        height: 18px;
        text-align: center;
        color: white;
        font-size: 9pt;
    }
    QProgressBar::chunk {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            from:#6c63ff, to:#a78bfa);
        border-radius: 6px;
    }
"""

DOWNLOAD_BTN_ACTIVE = """
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            from:#6c63ff, to:#a78bfa);
        color: white;
        border-radius: 10px;
        padding: 13px;
        font-size: 12pt;
        font-weight: bold;
        border: none;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            from:#7c73ff, to:#b79bff);
    }
    QPushButton:pressed {
        background: #5a52d5;
    }
"""

DOWNLOAD_BTN_DISABLED = """
    QPushButton {
        background-color: #1e1e2a;
        color: #444;
        border-radius: 10px;
        padding: 13px;
        font-size: 12pt;
        font-weight: bold;
        border: 2px solid #2a2a3a;
    }
"""

# Formato por tipo de contenido
FORMATS_VIDEO  = ["mp4", "mkv", "webm", "avi"]
FORMATS_AUDIO  = ["mp3", "m4a", "flac", "ogg", "wav"]
FORMATS_IMAGE  = ["jpg", "png", "webp", "gif", "bmp"]


def get_icon_path(icon_file: str) -> str:
    import sys
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(base, "assets", "apps", "link_converter", icon_file)


# ─────────────────────────────────────────────────────────────────────────────
#  Ventana principal
# ─────────────────────────────────────────────────────────────────────────────
class LinkConverterWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Link Converter")
        self.setGeometry(120, 120, 520, 660)
        apply_window_theme(self)
        self._colors = get_app_colors()

        self._worker           = None
        self._media_type       = "video"          # "video" | "audio" | "image"
        self._current_platform = None
        self._allowed_types    = ["video", "audio", "image"]  # actualizado por detector

        self.init_ui()

    # ── UI ────────────────────────────────────────────────────────────────────
    def init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(26, 24, 26, 24)
        card, layout = make_card_container()

        # ── Barra superior ──────────────────────────────────────────────────
        top = QHBoxLayout()
        back_btn = QPushButton("← Volver")
        back_btn.setFixedWidth(90)
        back_btn.clicked.connect(self.go_back)
        back_btn.setStyleSheet(get_soft_button_style())
        top.addWidget(back_btn)
        top.addStretch()
        layout.addLayout(top)

        # ── Título ──────────────────────────────────────────────────────────
        title = QLabel("Link Converter")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"color: {self._colors['text_main']}; font-size: 16pt; font-weight: 700;")
        layout.addWidget(title)

        self.subtitle = QLabel("Descarga video, audio o imagen desde redes sociales")
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle.setStyleSheet(
            f"color: {self._colors['text_muted']}; font-size: 9pt;")
        layout.addWidget(self.subtitle)

        # ── Logo de plataforma ──────────────────────────────────────────────
        self.platform_logo = QLabel()
        self.platform_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.platform_logo.setFixedHeight(90)
        self._clear_logo()
        layout.addWidget(self.platform_logo)

        self.platform_name_label = QLabel("")
        self.platform_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.platform_name_label.setStyleSheet(
            f"color: {self._colors['text_muted']}; font-size: 9pt;")
        layout.addWidget(self.platform_name_label)

        # ── Badge de tipo detectado ─────────────────────────────────────────
        self.detected_badge = QLabel("")
        self.detected_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detected_badge.setVisible(False)
        layout.addWidget(self.detected_badge)

        # ── Campo URL ───────────────────────────────────────────────────────
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(
            "Pega aquí el enlace (YouTube, TikTok, Instagram, imagen...)")
        self.url_input.setStyleSheet(URL_INPUT_STYLE)
        self.url_input.textChanged.connect(self._on_url_changed)
        layout.addWidget(self.url_input)

        # ── Separador ───────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #3a3a52;")
        layout.addWidget(sep)

        # ── Tipo de descarga ─────────────────────────────────────────────────
        type_label = QLabel("Tipo de descarga:")
        type_label.setStyleSheet(
            f"color: {self._colors['text_muted']}; font-size: 9pt;")
        layout.addWidget(type_label)

        type_row = QHBoxLayout()

        self.btn_video = QPushButton("🎬  Video")
        self.btn_video.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_video.clicked.connect(lambda: self._set_type("video"))

        self.btn_audio = QPushButton("🎵  Audio")
        self.btn_audio.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_audio.clicked.connect(lambda: self._set_type("audio"))

        self.btn_image = QPushButton("🖼  Imagen")
        self.btn_image.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_image.clicked.connect(lambda: self._set_type("image"))

        type_row.addWidget(self.btn_video)
        type_row.addWidget(self.btn_audio)
        type_row.addWidget(self.btn_image)
        layout.addLayout(type_row)
        self._update_type_buttons()

        # ── Formato + Calidad ────────────────────────────────────────────────
        options_row = QHBoxLayout()

        fmt_col = QVBoxLayout()
        fmt_lbl = QLabel("Formato:")
        fmt_lbl.setStyleSheet(f"color: {self._colors['text_muted']}; font-size: 9pt;")
        self.fmt_combo = QComboBox()
        self.fmt_combo.setStyleSheet(COMBO_STYLE_LC)
        self._populate_format_combo()
        fmt_col.addWidget(fmt_lbl)
        fmt_col.addWidget(self.fmt_combo)
        options_row.addLayout(fmt_col)

        options_row.addSpacing(20)

        qual_col = QVBoxLayout()
        qual_lbl = QLabel("Calidad (video):")
        qual_lbl.setStyleSheet(f"color: {self._colors['text_muted']}; font-size: 9pt;")
        self.quality_lbl = qual_lbl
        self.qual_combo = QComboBox()
        self.qual_combo.setStyleSheet(COMBO_STYLE_LC)
        self.qual_combo.addItems(["Mejor disponible", "1080p", "720p", "480p", "360p"])
        qual_col.addWidget(qual_lbl)
        qual_col.addWidget(self.qual_combo)
        options_row.addLayout(qual_col)

        layout.addLayout(options_row)

        # ── Progreso ─────────────────────────────────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(PROGRESS_STYLE)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(
            f"color: {self._colors['text_muted']}; font-size: 9pt;")
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        # ── Botón Descargar ──────────────────────────────────────────────────
        self.download_btn = QPushButton("⬇  Descargar")
        self.download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.download_btn.clicked.connect(self._start_download)
        layout.addWidget(self.download_btn)
        self._update_download_btn()

        outer.addWidget(card)
        self.setLayout(outer)

    # ── Lógica de URL / plataforma ────────────────────────────────────────────
    def _on_url_changed(self, text: str):
        text = text.strip()
        if not text:
            self._clear_logo()
            self.platform_name_label.setText("")
            self.detected_badge.setVisible(False)
            self._allowed_types = ["video", "audio", "image"]
            self._set_type("video")
            self._update_download_btn()
            return

        name, icon, content_type, allow_types = detect_platform(text)
        self._allowed_types    = allow_types
        self._current_platform = name

        # Logo
        if icon:
            pix = QPixmap(get_icon_path(icon))
            if not pix.isNull():
                self.platform_logo.setPixmap(
                    pix.scaled(80, 80,
                               Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation))
            else:
                self._clear_logo()
        else:
            self._clear_logo()

        self.platform_name_label.setText(name)

        # Badge de tipo detectado
        self._update_detected_badge(content_type)

        # Forzar tipo si solo hay uno permitido
        if len(allow_types) == 1:
            self._set_type(allow_types[0])
        elif self._media_type not in allow_types:
            # El tipo actual no está permitido → seleccionar el primero disponible
            self._set_type(allow_types[0])
        else:
            self._update_type_buttons()

        self._update_download_btn()

    def _update_detected_badge(self, content_type: str):
        """Muestra un badge indicando qué tipo de contenido fue detectado."""
        if content_type == "image":
            self.detected_badge.setText("🖼  Contenido detectado: IMAGEN — solo puedes descargar imágenes")
            self.detected_badge.setStyleSheet(
                "color: #38ef7d; font-size: 9pt; font-weight: bold;")
            self.detected_badge.setVisible(True)
        elif content_type == "audio":
            self.detected_badge.setText("🎵  Contenido detectado: AUDIO — solo puedes descargar audio")
            self.detected_badge.setStyleSheet(
                "color: #a78bfa; font-size: 9pt; font-weight: bold;")
            self.detected_badge.setVisible(True)
        elif content_type == "video":
            self.detected_badge.setText("🎬  Contenido detectado: VIDEO — puedes descargar video o audio")
            self.detected_badge.setStyleSheet(
                "color: #6c63ff; font-size: 9pt; font-weight: bold;")
            self.detected_badge.setVisible(True)
        else:
            # "any" — no mostrar badge restrictivo
            self.detected_badge.setVisible(False)

    def _clear_logo(self):
        self.platform_logo.clear()
        self.platform_logo.setText("🔗")
        self.platform_logo.setStyleSheet(
            f"font-size: 48pt; color: {self._colors['text_muted']};")

    # ── Tipo Video / Audio / Imagen ───────────────────────────────────────────
    def _set_type(self, t: str):
        self._media_type = t
        self._update_type_buttons()
        self._populate_format_combo()
        # La calidad solo aplica a video
        qual_visible = (t == "video")
        self.qual_combo.setVisible(qual_visible)
        self.quality_lbl.setVisible(qual_visible)

    def _update_type_buttons(self):
        muted = self._colors["text_muted"]

        def _style_btn(btn, btn_type, active_style=TYPE_BTN_ACTIVE):
            allowed = btn_type in self._allowed_types
            is_active = (self._media_type == btn_type)

            if not allowed:
                btn.setStyleSheet(TYPE_BTN_DISABLED)
                btn.setEnabled(False)
                btn.setCursor(Qt.CursorShape.ForbiddenCursor)
            else:
                btn.setEnabled(True)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                if is_active:
                    btn.setStyleSheet(active_style)
                else:
                    btn.setStyleSheet(
                        TYPE_BTN_INACTIVE_TMPL.format(muted=muted))

        _style_btn(self.btn_video, "video", TYPE_BTN_ACTIVE)
        _style_btn(self.btn_audio, "audio", TYPE_BTN_ACTIVE)
        _style_btn(self.btn_image, "image", TYPE_BTN_ACTIVE_IMG)

    def _populate_format_combo(self):
        self.fmt_combo.clear()
        if self._media_type == "video":
            self.fmt_combo.addItems(FORMATS_VIDEO)
        elif self._media_type == "audio":
            self.fmt_combo.addItems(FORMATS_AUDIO)
        else:
            self.fmt_combo.addItems(FORMATS_IMAGE)

    # ── Botón Descargar ───────────────────────────────────────────────────────
    def _update_download_btn(self):
        has_url = bool(self.url_input.text().strip())
        if has_url:
            self.download_btn.setEnabled(True)
            self.download_btn.setStyleSheet(DOWNLOAD_BTN_ACTIVE)
        else:
            self.download_btn.setEnabled(False)
            self.download_btn.setStyleSheet(DOWNLOAD_BTN_DISABLED)

    # ── Descarga ──────────────────────────────────────────────────────────────
    def _start_download(self):
        url = self.url_input.text().strip()
        if not url:
            return

        output_dir = QFileDialog.getExistingDirectory(
            self, "Seleccionar carpeta de descarga")
        if not output_dir:
            return

        fmt = self.fmt_combo.currentText()
        quality_map = {
            "Mejor disponible": "best",
            "1080p": "1080", "720p": "720",
            "480p": "480",   "360p": "360",
        }
        quality = quality_map.get(self.qual_combo.currentText(), "best")

        # Advertencia si descarga de imagen desde plataforma de video
        if self._media_type == "image" and self._allowed_types != ["image"]:
            ans = QMessageBox.question(
                self,
                "Descarga de imagen",
                "Intentarás descargar esta URL como imagen directa.\n"
                "Esto solo funciona con URLs que apunten directamente a un archivo de imagen.\n\n"
                "¿Continuar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if ans != QMessageBox.StandardButton.Yes:
                return

        # Preparar UI
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setVisible(True)
        self.status_label.setText("Iniciando descarga...")
        self.download_btn.setEnabled(False)
        self.download_btn.setStyleSheet(DOWNLOAD_BTN_DISABLED)
        self.url_input.setEnabled(False)
        QApplication.processEvents()

        from apps.link_converter.downloader import DownloadWorker
        self._worker = DownloadWorker(
            url=url,
            media_type=self._media_type,
            fmt=fmt,
            quality=quality,
            output_dir=output_dir,
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(
            lambda title: self._on_finished(title, output_dir))
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_progress(self, percent: int, text: str):
        self.progress_bar.setValue(percent)
        self.status_label.setText(text)

    def _on_finished(self, title: str, output_dir: str):
        self.progress_bar.setValue(100)
        self.status_label.setText("✅ ¡Descarga completada!")
        self._reset_ui()
        QMessageBox.information(
            self,
            "Descarga completada",
            f"✅ Descargado correctamente:\n\n\"{title}\"\n\nGuardado en:\n{output_dir}",
        )
        try:
            os.startfile(output_dir)
        except Exception:
            try:
                subprocess.Popen(["xdg-open", output_dir])
            except Exception:
                pass

    def _on_error(self, message: str):
        self.progress_bar.setVisible(False)
        self.status_label.setVisible(False)
        self._reset_ui()
        QMessageBox.critical(
            self,
            "Error en la descarga",
            f"❌ No se pudo completar la descarga:\n\n{message}",
        )

    def _reset_ui(self):
        self.url_input.setEnabled(True)
        self._update_download_btn()

    # ── Navegación ────────────────────────────────────────────────────────────
    def go_back(self):
        from core.ui.hub_window import HubWindow
        self.hub = HubWindow()
        self.hub.show()
        self.close()
